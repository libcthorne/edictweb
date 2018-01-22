import os
from datetime import datetime

import django
from celery import Celery

from importer import const
from importer.util import normalize_query, normalize_word

################################################################

# Setup Django before importing models. Note: not a problem for
# initialized apps importing this file because setup does nothing if
# it was already called previously.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edictweb.settings')
django.setup()

################################################################

from importer.models import (
    DictionaryEntry,
    DictionaryEntryMatch,
    InvertedIndexEntry,
)

app = Celery(__name__, broker='amqp://guest@localhost//')

def cleanup_tasks():
    app.control.purge()

@app.task(autoretry_for=(Exception,))
def index_dictionary_entry_by_id(dictionary_entry_id):
    try:
        dictionary_entry = DictionaryEntry.objects.get(id=dictionary_entry_id)
    except DictionaryEntry.DoesNotExist:
        print("Unknown dictionary entry %s for index request" % dictionary_entry_id)
        return

    # Extract Japanese forms and English glosses from raw edict data
    jp_text = dictionary_entry.jp_text
    en_text = dictionary_entry.en_text

    # Split Japanese text string into descriptions
    # e.g. "〃;おなじ;おなじく" -> ["〃", "おなじ", "おなじく"]
    jp_text_descriptions = jp_text.split(const.JP_TEXT_DESCRIPTION_SEPARATOR)

    # Split English text string into descriptons
    # e.g. "to total/to sum" -> ["to total", "to sum"]
    en_text_descriptions = en_text.split(const.EN_TEXT_DESCRIPTION_SEPARATOR)

    # Build index entries from en and jp text
    save_start = datetime.now()
    entries = _build_index_entries(dictionary_entry, [jp_text_descriptions, en_text_descriptions])

    for word_ngram, weight in entries.items():
        InvertedIndexEntry.objects(
            index_word_text=word_ngram,
            import_request_id=dictionary_entry.import_request_id,
        ).update(
            push__matches=DictionaryEntryMatch(
                dictionary_entry=dictionary_entry,
                weight=weight,
            ),
            upsert=True,
        )

    save_end = datetime.now()

    print("Saved {} index entries in {}".format(len(entries), save_end-save_start))

def _build_index_entries(dictionary_entry, descriptions_collection):
    """
    Builds index entries for a given dictionary entry from a
    collection of descriptions. Descriptions can be a list of English
    definitions ("glosses") with words separated by spaces, e.g.
    ["stray cat", "alley cat"] or a list of Japanese forms, e.g.  ["野
    良猫", "のらねこ"].
    """
    # Collection of index entries built, mapped by word
    entries = {}

    for descriptions in descriptions_collection:
        for description_index, raw_description in enumerate(descriptions):
            description = normalize_query(raw_description)
            description_words = description.split(const.DESCRIPTION_WORD_SEPARATOR)

            for word_index, raw_word in enumerate(description_words):
                word = normalize_word(raw_word)
                if not word:
                    continue # word is not indexable

                # Index each edge n-gram (i.e. quick -> q, qu, qui, quic, quick)
                for i in range(len(word)):
                    word_ngram = word[:i+1]

                    weight = 1.0

                    match_rate = len(word_ngram)/len(word)
                    if match_rate == 1:
                        # Exact matches should have larger weight
                        weight += 3
                    else:
                        # Partial matches should have smaller weight
                        weight += 1*match_rate

                    # Matches in short descriptions should have larger weight
                    weight += 1*(max(4-len(description_words), 1)/3)

                    # Matches in earlier occurring words should have larger weight
                    weight += 1*(max(3-word_index, 1)/3)

                    # Matches in earlier occurring descriptions should have larger weight
                    weight += 2*((len(descriptions)-description_index)/len(descriptions))

                    # Common words should have larger weight
                    if dictionary_entry.frequency_rank:
                        frequency_scale = max(
                            (const.MAX_FREQUENCY_RANK+1)
                            - dictionary_entry.frequency_rank,
                            1
                        )/const.MAX_FREQUENCY_RANK
                        weight += 2*frequency_scale

                    if word_ngram not in entries or weight > entries[word_ngram]:
                        entries[word_ngram] = weight

    return entries
