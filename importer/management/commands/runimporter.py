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
                task_thread = threading.Thread(target=self.run_task, args=(task_id,))
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

    def run_task(self, task_id):
        self.stdout.write("Deleting existing dictionary entries")
        DictionaryEntry.objects.all().delete()

        self.stdout.write("Starting dictionary file import")

        with open(DICTIONARY_FILE, 'r', encoding='euc-jp') as f:
            header_line = f.readline()

            for entry_line in f:
                entry = DictionaryEntry(edict_data=entry_line)
                entry.save()

                if self.last_requested_task_id != task_id:
                    self.stdout.write("Task interrupted")
                    break # interrupt task

                # set progress
            else:
                # set done
                pass

        self.stdout.write("Finished dictionary file import")

        self.task_lock.release()
