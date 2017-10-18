import codecs
import threading
import time

from django.core.management.base import BaseCommand

from importer.models import (
    DictionaryEntry,
    DictionaryImportRequest,
)

DICTIONARY_FILE = 'edict2'
TASK_POLL_INTERVAL = 5

class Command(BaseCommand):
    help = 'Polls for and processes dictionary import requests'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_requested_task_id = None
        self.task_lock = threading.Lock()

    def handle(self, *args, **kwargs):
        while True:
            task_id = self.get_pending_task()

            if task_id != self.last_requested_task_id:
                # interrupt current task
                self.last_requested_task_id = task_id

                # wait for current task to stop
                self.task_lock.acquire()

                # start new task thread
                task_thread = threading.Thread(target=self.start_task, args=(task_id,))
                task_thread.start()
            else:
                self.stdout.write("No new task")

            time.sleep(TASK_POLL_INTERVAL)

    def get_pending_task(self):
        try:
            latest_task = DictionaryImportRequest.objects.latest('id')
            if not latest_task.completed:
                return latest_task.id
        except DictionaryImportRequest.DoesNotExist:
            pass

    def start_task(self, task_id):
        try:
            self.run_task(task_id)
        except DictionaryImportRequest.DoesNotExist:
            pass

        self.task_lock.release()

    def run_task(self, task_id):
        # Mark request as started
        request = DictionaryImportRequest.objects.get(id=task_id)
        request.started = True
        request.save()

        # Remove existing dictionary entries
        self.stdout.write("[Task %d] Deleting existing dictionary entries" % task_id)
        DictionaryEntry.objects.all().delete()

        self.stdout.write("[Task %d] Starting dictionary file import" % task_id)

        # Read and save new dictionary entries
        with codecs.open(DICTIONARY_FILE, 'r', encoding='euc-jp') as f:
            # Read and ignore header
            header_line = f.readline()

            # Count and save total number of entries
            first_entry_pos = f.tell()
            total_entry_lines = sum(1 for l in f)
            request = DictionaryImportRequest.objects.get(id=task_id)
            request.total_entries_count = total_entry_lines
            request.save()

            # Read entry lines
            f.seek(first_entry_pos)
            for entry_index, entry_line in enumerate(f):
                # Check if task should still be running
                if self.last_requested_task_id != task_id:
                    self.stdout.write("[Task %d] Task interrupted" % task_id)
                    request = DictionaryImportRequest.objects.get(id=task_id)
                    request.interrupted = True
                    request.save()
                    break # interrupt task

                # Create and save new entry
                entry = DictionaryEntry(edict_data=entry_line)
                entry.save()
                self.stdout.write("[Task %d] Saved %d/%d entry lines" % (task_id, entry_index+1, total_entry_lines))

                # Log progress
                progress = (entry_index+1)/total_entry_lines
                self.stdout.write("[Task %d] Progress: %.2f%%" % (task_id, progress*100))
            else:
                # Task finished, mark as completed
                request = DictionaryImportRequest.objects.get(id=task_id)
                request.completed = True
                request.save()

        self.stdout.write("Finished dictionary file import")
