import os
from datetime import datetime

import django
from celery import Celery

################################################################

# Setup Django before importing models. Note: not a problem for
# initialized apps importing this file because setup does nothing if
# it was already called previously.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edictweb.settings')
django.setup()

################################################################

from .models import (
    DictionaryEntry,
    InvertedIndexEntry,
)

app = Celery(__name__, broker='amqp://guest@localhost//')

@app.task(autoretry_for=(Exception,))
def index_dictionary_entry_by_id(dictionary_entry_id):
    try:
        dictionary_entry = DictionaryEntry.objects.get(id=dictionary_entry_id)
    except DictionaryEntry.DoesNotExist:
        print("Unknown dictionary entry %d for index request" % dictionary_entry_id)
        return

    raw_edict_data = str(dictionary_entry.edict_data)
    edict_data = InvertedIndexEntry.normalize_query(raw_edict_data)

    # Index entry words

    # keep track of the previous word's start_position to enable
    # correct search of start_position for words contained in data
    # more than once
    prev_start_position = -1

    entries = []

    for raw_word in edict_data.split(' '):
        start_position = raw_edict_data.index(raw_word, prev_start_position+1)
        prev_start_position = start_position
        word = InvertedIndexEntry.normalize_word(raw_word)
        if not word:
            continue # word is not indexable

        # Index each edge n-gram (i.e. quick -> q, qu, qui, quic, quick)
        for i in range(len(word)):
            word_ngram = word[:i+1]
            end_position = start_position+len(word_ngram)
            #print("Indexing %s under %s (start:%d, end:%d)" % (edict_data, word_ngram, start_position, end_position))
            inverted_index_entry = InvertedIndexEntry(
                index_word_text=word_ngram,
                dictionary_entry=dictionary_entry,
                start_position=start_position,
                end_position=end_position,
            )
            entries.append(inverted_index_entry)

    save_start = datetime.now()
    InvertedIndexEntry.objects.bulk_create(entries)
    save_end = datetime.now()

    print("Saved {} index entries in {}".format(len(entries), save_end-save_start))
