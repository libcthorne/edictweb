import time
import re
from datetime import datetime
from xml.etree.ElementTree import iterparse

from django.core.management.base import BaseCommand
from django.db import IntegrityError

from importer import const
from importer.models import (
    DictionaryEntry,
    DictionaryImportRequest,
    InvertedIndexEntry,
    PendingDictionaryImportRequest,
)
from importer.tasks import index_dictionary_entry_by_id

IMPORT_REQUEST_POLL_INTERVAL = 5

FREQUENCY_STRING_REGEX = re.compile("nf[0-9][0-9]")

def parse_frequency_rank(priority_elems):
    min_rank = None

    for priority_elem in priority_elems:
        priority_str = priority_elem.text
        rank = None

        if priority_str == "ichi1":
            rank = 10
        elif priority_str == "ichi2":
            rank = 20
        elif FREQUENCY_STRING_REGEX.search(priority_str):
            rank = int(priority_str[2:])

        if rank is not None:
            if min_rank is not None:
                min_rank = min(rank, min_rank)
            else:
                min_rank = rank

    if min_rank is not None:
        return min(min_rank, const.MAX_FREQUENCY_RANK)

def parse_entry(elem):
    sequence_number = int(elem.find("ent_seq").text)
    en_text = ""
    jp_text = ""
    meta_text = ""
    min_frequency_rank = None

    kanji_elems = elem.findall("k_ele")
    for kanji_elem in kanji_elems:
        kanji = kanji_elem.find("keb").text
        jp_text += kanji
        jp_text += const.JP_TEXT_DESCRIPTION_SEPARATOR

        frequency_rank = parse_frequency_rank(kanji_elem.findall("ke_pri"))
        if frequency_rank is not None:
            if min_frequency_rank is not None:
                min_frequency_rank = min(frequency_rank, min_frequency_rank)
            else:
                min_frequency_rank = frequency_rank

    reading_elems = elem.findall("r_ele")
    for index, reading_elem in enumerate(reading_elems):
        reading = reading_elem.find("reb").text
        jp_text += reading
        if index+1 < len(reading_elems):
            jp_text += const.JP_TEXT_DESCRIPTION_SEPARATOR

        frequency_rank = parse_frequency_rank(reading_elem.findall("re_pri"))
        if frequency_rank is not None:
            if min_frequency_rank is not None:
                min_frequency_rank = min(frequency_rank, min_frequency_rank)
            else:
                min_frequency_rank = frequency_rank

    sense_elems = elem.findall("sense")
    for sense_index, sense_elem in enumerate(sense_elems):
        pos_elems = sense_elem.findall("pos")
        for pos_index, pos_elem in enumerate(pos_elems):
            meta_text += pos_elem.text
            if pos_index+1 < len(pos_elems):
                meta_text += const.META_TEXT_SEPARATOR

        gloss_elems = sense_elem.findall("gloss")
        for gloss_index, gloss_elem in enumerate(gloss_elems):
            en_text += gloss_elem.text
            if gloss_index+1 < len(gloss_elems):
                en_text += const.EN_TEXT_DESCRIPTION_SEPARATOR

        if sense_index+1 < len(sense_elems):
            en_text += const.EN_TEXT_DESCRIPTION_SEPARATOR

    return sequence_number, en_text, jp_text, meta_text, min_frequency_rank

def process_import_request(import_request_id):
    # Mark request as started
    import_request = DictionaryImportRequest.objects.get(id=import_request_id)
    import_request.started = True
    import_request.save()

    # Remove existing dictionary entries
    print("[Request %d] Deleting existing dictionary entries" % import_request_id)
    DictionaryEntry.objects.all().delete()
    InvertedIndexEntry.objects.all().delete()

    print("[Request %d] Starting dictionary file import" % import_request_id)

    import_start_time = datetime.now()

    context = iterparse(const.DICTIONARY_FILE, events=("start", "end"))
    context = iter(context)
    _, root = next(context)
    entry_index = 0
    for event, elem in context:
        if event == "start":
            continue

        if elem.tag != "entry":
            continue

        (
            sequence_number,
            en_text,
            jp_text,
            meta_text,
            min_frequency_rank,
        ) = parse_entry(elem)

        # Create and save new entry
        entry = DictionaryEntry(
            jp_text=jp_text,
            en_text=en_text,
            meta_text=meta_text,
            sequence_number=sequence_number,
            frequency_rank=min_frequency_rank,
            common=min_frequency_rank is not None,
        )
        entry.save()
        print("[Request %d] Saved %d entry lines" % (import_request_id, entry_index+1))

        # Add to index
        index_dictionary_entry_by_id.apply_async(args=(str(entry.id),))

        # Log progress
        print("[Request %d] Progress: %d entries saved" % (import_request_id, entry_index+1))

        # Remove entry from root tree to keep memory usage low
        root.clear()

        entry_index += 1

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

    print("[Request %d] Finished dictionary file import in (entries: %d, duration: %s)" % (
        import_request_id,
        entry_index,
        import_duration,
    ))

def get_pending_import_request_id():
    return PendingDictionaryImportRequest.objects.first().import_request_id

class Command(BaseCommand):
    help = 'Polls for and processes dictionary import requests'

    def handle(self, *args, **kwargs):
        while True:
            import_request_id = get_pending_import_request_id()

            if import_request_id:
                try:
                    process_import_request(import_request_id)
                except (DictionaryImportRequest.DoesNotExist, IntegrityError) as e:
                    self.stdout.write("[Request %d] Import request interrupted" % import_request_id)
            else:
                self.stdout.write("No pending import request")

            time.sleep(IMPORT_REQUEST_POLL_INTERVAL)
