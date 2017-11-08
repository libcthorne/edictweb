from .models import (
    DictionaryEntry,
    InvertedIndexEntry,
    InvertedIndexWord,
)

def index_dictionary_entry(dictionary_entry):
    raw_edict_data = str(dictionary_entry.edict_data)
    edict_data = InvertedIndexWord.normalize_query(raw_edict_data)

    # Index entry words

    # keep track of the previous word's start_position to enable
    # correct search of start_position for words contained in data
    # more than once
    prev_start_position = -1

    entries = []

    for raw_word in edict_data.split(' '):
        start_position = raw_edict_data.index(raw_word, prev_start_position+1)
        prev_start_position = start_position
        word = InvertedIndexWord.normalize_word(raw_word)
        if not word:
            continue # word is not indexable

        # Index each edge n-gram (i.e. quick -> q, qu, qui, quic, quick)
        for i in range(len(word)):
            word_ngram = word[:i+1]
            end_position = start_position+len(word_ngram)
            #print("Indexing %s under %s (start:%d, end:%d)" % (edict_data, word_ngram, start_position, end_position))
            inverted_index_word, _ = InvertedIndexWord.objects.get_or_create(word=word_ngram)
            inverted_index_entry = InvertedIndexEntry(
                index_word=inverted_index_word,
                dictionary_entry=dictionary_entry,
                start_position=start_position,
                end_position=end_position,
            )
            entries.append(inverted_index_entry)

    InvertedIndexEntry.objects.bulk_create(entries)