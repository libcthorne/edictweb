import logging

from .models import DictionaryEntry

logger = logging.getLogger(__name__)

def delete_existing_dictionary_entries():
    logger.info("Deleting existing dictionary entries")
    DictionaryEntry.objects.all().delete()

def import_dictionary_file(filename):
    delete_existing_dictionary_entries()

    logger.info("Starting dictionary file import")

    with open(filename, 'r', encoding='euc-jp') as f:
        header_line = f.readline()

        for entry_line in f:
            entry = DictionaryEntry(edict_data=entry_line)
            entry.save()

    logger.info("Finished dictionary file import")
