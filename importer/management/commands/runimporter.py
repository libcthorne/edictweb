import time

from django.core.management.base import BaseCommand
from mongoengine.errors import OperationError

from importer import tasks

IMPORT_REQUEST_POLL_INTERVAL = 5

class Command(BaseCommand):
    help = 'Polls for and processes dictionary import requests'

    def handle(self, *args, **kwargs):
        while True:
            import_request_id = tasks.get_pending_import_request_id()

            if import_request_id:
                try:
                    tasks.process_import_request(import_request_id)
                except OperationError:
                    self.stdout.write("[Request %d] Import request interrupted" % import_request_id)
            else:
                self.stdout.write("No pending import request")

            time.sleep(IMPORT_REQUEST_POLL_INTERVAL)
