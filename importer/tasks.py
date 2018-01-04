import os
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
    jp_text = dictionary_entry.jp_text
    en_text = dictionary_entry.en_text

    # Split Japanese forms string into array, e.g.
    # e.g. "〃;おなじ;おなじく" -> ["〃", "おなじ", "おなじく"]
    jp_text_forms = jp_text.split(";")

    # Split English glosses string into array
    # e.g. "to total/to sum" -> ["to total", "to sum"]
    en_text_glosses = en_text.split("/")

    # Build index entries from forms and glosses
    entries = (
        _build_index_entries(dictionary_entry, jp_text_forms, 'jp_text')
        + _build_index_entries(dictionary_entry, en_text_glosses, 'en_text')
    )

    # Save index entries
    save_start = datetime.now()
    InvertedIndexEntry.objects.bulk_create(entries)
    save_end = datetime.now()

    print("Saved {} index entries in {}".format(len(entries), save_end-save_start))

def _build_index_entries(dictionary_entry, descriptions, index_column):
    """
    Builds InvertedIndexEntry objects for a given dictionary entry
    from a list of descriptions. Descriptions can be a list of English
    definitions ("glosses") with words separated by spaces, e.g.
    ["stray cat", "alley cat"] or a list of Japanese forms, e.g.
    ["野良猫", "のらねこ"].

    Index column is the name of the column that contains the string
    being indexed, e.g. "jp_text" or "en_text". This string is used to
    determine where a description match occurs for highlighting
    purposes.
    """
    index_context = getattr(dictionary_entry, index_column)

    # Keep track of the previous word's start_position to enable
    # correct search of start_position in index_context for words
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

            start_position = index_context.index(raw_word, prev_start_position+1)
            prev_start_position = start_position

            # Index each edge n-gram (i.e. quick -> q, qu, qui, quic, quick)
            for i in range(len(word)):
                word_ngram = word[:i+1]
                end_position = start_position+len(word_ngram)

                weight = 1.0

                # Exact matches should have larger weight
                # Partial matches should have smaller weight
                match_rate = len(word_ngram)/len(word)
                weight *= 3 if match_rate == 1 else match_rate

                # Matches in a long description should have smaller weight
                weight /= min(len(description_words), 3)

                # Common words should have larger weight
                if dictionary_entry.frequency_rank:
                    frequency_scale = max(51-dictionary_entry.frequency_rank, 1)/50
                    weight += 1.5*frequency_scale

                inverted_index_entry = InvertedIndexEntry(
                    index_word_text=word_ngram,
                    dictionary_entry=dictionary_entry,
                    start_position=start_position,
                    end_position=end_position,
                    weight=weight,
                    index_column=index_column,
                )
                entries.append(inverted_index_entry)

    return entries
