import re
import string
import unicodedata

from django.db import models

class DictionaryImportRequest(models.Model):
    started = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    total_entries_count = models.PositiveIntegerField(default=0)

class PendingDictionaryImportRequest(models.Model):
    """
    Points to a dictionary import request that needs processing. The
    application should assume that a single row always exists and
    treat import_request being null as the lack of a pending request.
    """
    import_request = models.OneToOneField(DictionaryImportRequest, on_delete=models.SET_NULL, null=True)

class DictionaryEntry(models.Model):
    edict_data = models.CharField(max_length=2048)

    # Foreign key constraint with ON DELETE CASCADE manually set
    # See migration 0015_auto_20171031_2020.py
    source_import_request = models.ForeignKey(DictionaryImportRequest, on_delete=models.CASCADE, db_constraint=False)

    def __str__(self):
        return self.edict_data

class InvertedIndexEntry(models.Model):
    index_word_text = models.CharField(max_length=128, db_index=True)

    # Foreign key constraint with ON DELETE CASCADE manually set
    # See migration 0015_auto_20171031_2020.py
    dictionary_entry = models.ForeignKey(DictionaryEntry, on_delete=models.CASCADE, db_constraint=False)

    start_position = models.PositiveIntegerField()
    end_position = models.PositiveIntegerField()

    weight = models.FloatField()

    @staticmethod
    def normalize_query(query):
        return re.sub(r'[;/()\[\[]', ' ', query)

    @staticmethod
    def normalize_word(word):
        # strip trailing whitespace
        word = word.rstrip()
        # make case-insensitive
        word = word.lower()
        # normalize for full-width to half-width conversion, among other things
        word = unicodedata.normalize('NFKC', word)
        # remove punctuation characters
        word = ''.join(c for c in word if c not in string.punctuation)

        return word

    def __str__(self):
        return "Index of '{}' for {}".format(self.index_word_text, self.dictionary_entry)
