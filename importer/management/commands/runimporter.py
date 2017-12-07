import codecs
import re
import time
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import IntegrityError

from importer.models import (
    DictionaryEntry,
    DictionaryImportRequest,
    PendingDictionaryImportRequest,
)
from importer.tasks import index_dictionary_entry_by_id
from importer.util import sequence_number_from_str

DICTIONARY_FILE = 'edict2'
EDICT_METADATA_REGEX = re.compile("((\([a-z][a-z0-9-,]*\) )+(\{[a-z0-9-,]+\} )*)")
EDICT_P_GLOSS_REGEX = re.compile("/\(P\)$")
IMPORT_REQUEST_POLL_INTERVAL = 5

class Command(BaseCommand):
    help = 'Polls for and processes dictionary import requests'

    def handle(self, *args, **kwargs):
        while True:
            import_request_id = self.get_pending_import_request_id()
            if import_request_id:
                try:
                    self.process_import_request(import_request_id)
                except (DictionaryImportRequest.DoesNotExist, IntegrityError) as e:
                    self.stdout.write("[Request %d] Import request interrupted" % import_request_id)
            else:
                self.stdout.write("No pending import request")

            time.sleep(IMPORT_REQUEST_POLL_INTERVAL)

    def get_pending_import_request_id(self):
        return PendingDictionaryImportRequest.objects.first().import_request_id

    def process_import_request(self, import_request_id):
        # Mark request as started
        import_request = DictionaryImportRequest.objects.get(id=import_request_id)
        import_request.started = True
        import_request.save()

        # Remove existing dictionary entries
        self.stdout.write("[Request %d] Deleting existing dictionary entries" % import_request_id)
        DictionaryEntry.objects.all().delete()

        self.stdout.write("[Request %d] Starting dictionary file import" % import_request_id)

        import_start_time = datetime.now()

        # Read and save new dictionary entries
        with codecs.open(DICTIONARY_FILE, 'r', encoding='euc-jp') as f:
            # Read and ignore header
            header_line = f.readline()

            # Count and save total number of entries
            first_entry_pos = f.tell()
            total_entry_lines = sum(1 for l in f)
            import_request = DictionaryImportRequest.objects.get(id=import_request_id)
            import_request.total_entries_count = total_entry_lines
            import_request.save()

            # Read entry lines
            f.seek(first_entry_pos)
            for entry_index, entry_line in enumerate(f):
                edict_data, sequence_number_str, _ = entry_line.rsplit('/', 2)
                sequence_number = sequence_number_from_str(sequence_number_str)

                # Split JP/EN/meta text
                jp_text, en_text = edict_data.split(' /', 1)
                meta_text_matches = EDICT_METADATA_REGEX.findall(en_text)
                meta_text = ""
                for meta_text_match in meta_text_matches:
                    meta_text += meta_text_match[0]
                meta_text = meta_text.rstrip()

                # Format JP text to make indexing simpler
                jp_text = jp_text.replace(" [", ";") # convert kana readings into same form as kanji forms
                jp_text = jp_text.replace("]", "") # convert kana readings into same form as kanji forms

                # Format EN text to make indexing simpler
                en_text = EDICT_P_GLOSS_REGEX.sub("", en_text) # remove trailing (P) glosses

                # Create and save new entry
                entry = DictionaryEntry(
                    jp_text=jp_text,
                    en_text=en_text,
                    meta_text=meta_text,
                    sequence_number=sequence_number,
                    source_import_request=import_request,
                )
                entry.save()
                self.stdout.write("[Request %d] Saved %d/%d entry lines" % (import_request_id, entry_index+1, total_entry_lines))

                # Add to index
                index_dictionary_entry_by_id.apply_async(args=(entry.id,))

                # Log progress
                progress = (entry_index+1)/total_entry_lines
                self.stdout.write("[Request %d] Progress: %.2f%%" % (import_request_id, progress*100))

        # Request finished, mark as completed
        import_request = DictionaryImportRequest.objects.get(id=import_request_id)
        import_request.completed = True
        import_request.save()

        # Unmark import request as pending
        pending_import_request = PendingDictionaryImportRequest.objects.get(import_request=import_request)
        pending_import_request.import_request = None
        pending_import_request.save()

        import_finish_time = datetime.now()
        import_duration = import_finish_time - import_start_time

        self.stdout.write("[Request %d] Finished dictionary file import in (entries: %d, duration: %s)" % (
            import_request_id,
            total_entry_lines,
            import_duration,
        ))
