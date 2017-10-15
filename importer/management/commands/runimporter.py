import time

from django.core.management.base import BaseCommand

from importer.models import DictionaryEntry

DICTIONARY_FILE = 'edict2'
TASK_POLL_INTERVAL = 5

class Command(BaseCommand):
    help = 'Polls for and processes dictionary import requests'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active_task_id = None

    def handle(self, *args, **kwargs):
        while True:
            task_id = self.check_for_pending_task()

            if task_id != self.active_task_id:
                active_task_id = task_id # interrupt current task
                task_lock.acquire() # wait for current task to stop
                task_thread = Thread(self.run_task)
                task_thread.start()
            else:
                self.stdout.write("No new task")

            time.sleep(TASK_POLL_INTERVAL)

    def check_for_pending_task(self):
        return None

    def run_task(task_id):
        self.stdout.write("Deleting existing dictionary entries")
        DictionaryEntry.objects.all().delete()

        self.stdout.write("Starting dictionary file import")

        with open(filename, 'r', encoding='euc-jp') as f:
            header_line = f.readline()

            for entry_line in f:
                entry = DictionaryEntry(edict_data=entry_line)
                entry.save()

                if active_task_id != task_id:
                    break # interrupt task

                # set progress
            else:
                # set done
                pass

        self.stdout.write("Finished dictionary file import")

        task_lock.release()
