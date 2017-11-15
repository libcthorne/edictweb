import os
import re
from datetime import datetime

import django
from celery import Celery

from .util import normalize_query, normalize_word

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

    # Extract Japanese forms and English glosses from raw edict data
    raw_edict_data = str(dictionary_entry.edict_data)
    jp_text, en_text = raw_edict_data.split(" /", 1)

    # Parse Japanese forms string into array, e.g.
    # e.g. "〃 [おなじ;おなじく]" -> ["〃", "おなじ", "おなじく"]
    jp_text = re.sub("\([^\(]+\) ?", "", jp_text) # Temporary (removes reading->kanji link)
    jp_text = jp_text.replace(" [", ";") # Temporary (puts readings into same form as kanji forms)
    jp_text = jp_text.replace("]", "") # Temporary (puts readings into same form as kanji forms)
    jp_text_forms = jp_text.split(";")

    # Parse English glosses string into array
    # e.g. "{comp} (n) (v) to total/to sum (see xx)" -> ["to total", "to sum"]
    en_text = re.sub("\([^\(]+\) ?", "", en_text) # Temporary (removes (n) etc.)
    en_text = re.sub("\{[^{]+\} ?", "", en_text) # Temporary (removes {comp} etc.)
    en_text_glosses = en_text.split("/")

    # Build index entries from forms and glosses
    entries = (
        _build_index_entries(dictionary_entry, jp_text_forms)
        + _build_index_entries(dictionary_entry, en_text_glosses)
    )

    # Save index entries
    save_start = datetime.now()
    InvertedIndexEntry.objects.bulk_create(entries)
    save_end = datetime.now()

    print("Saved {} index entries in {}".format(len(entries), save_end-save_start))

def _build_index_entries(dictionary_entry, descriptions):
    """
    Builds InvertedIndexEntry objects for a given dictionary entry
    from a list of descriptions. Descriptions can be a list of English
    definitions ("glosses") with words separated by spaces, e.g.
    ["stray cat", "alley cat"] or a list of Japanese forms, e.g.
    ["野良猫", "のらねこ"].
    """
    #print("Build index entries for %s from %s" % (dictionary_entry, descriptions))

    # Edict data being indexed
    raw_edict_data = str(dictionary_entry.edict_data)

    # Keep track of the previous word's start_position to enable
    # correct search of start_position in edict_data for words
    # contained more than once
    prev_start_position = -1

    # Collection of index entries built
    entries = []

    for raw_description in descriptions:
        description = normalize_query(raw_description)
        description_words = description.split(' ')
        for raw_word in description_words:
            word = normalize_word(raw_word)
            if not word:
                continue # word is not indexable

            start_position = raw_edict_data.index(raw_word, prev_start_position+1)
            prev_start_position = start_position

            # Index each edge n-gram (i.e. quick -> q, qu, qui, quic, quick)
            for i in range(len(word)):
                word_ngram = word[:i+1]
                end_position = start_position+len(word_ngram)

                # Partial matches should have smaller weight
                weight = len(word_ngram)/len(word)
                # Matches in a long description should have smaller weight
                weight /= len(description_words)
                # More descriptions should reduce the weight of a single description match
                weight /= len(descriptions)

                #print("Indexing %s under %s (start:%d, end:%d, weight:%s)" % (raw_edict_data, word_ngram, start_position, end_position, weight))

                inverted_index_entry = InvertedIndexEntry(
                    index_word_text=word_ngram,
                    dictionary_entry=dictionary_entry,
                    start_position=start_position,
                    end_position=end_position,
                    weight=weight,
                )
                entries.append(inverted_index_entry)

    return entries
