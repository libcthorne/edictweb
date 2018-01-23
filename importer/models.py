import re

from django.db import models

from . import const
from .util import meta_info_to_label

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
    jp_text = models.CharField(max_length=2048)
    en_text = models.CharField(max_length=2048)
    meta_text = models.CharField(max_length=2048)
    sequence_number = models.PositiveIntegerField(db_index=True)
    frequency_rank = models.PositiveIntegerField(db_index=True, null=True)
    common = models.BooleanField(db_index=True)

    # Foreign key constraint with ON DELETE CASCADE manually set
    # See migration 0015_auto_20171031_2020.py
    source_import_request = models.ForeignKey(DictionaryImportRequest, on_delete=models.CASCADE, db_constraint=False)

    @property
    def meta_labels(self):
        meta_labels = set()
        meta_infos = self.meta_text.split(const.META_TEXT_SEPARATOR)
        for meta_info in meta_infos:
            meta_label = meta_info_to_label(meta_info)
            if meta_label:
                meta_labels.add(meta_label)
        return meta_labels

    def __str__(self):
        return self.jp_text + "|" + self.en_text

class InvertedIndexEntry(models.Model):
    index_word_text = models.CharField(max_length=256, db_index=True)

    # Foreign key constraint with ON DELETE CASCADE manually set
    # See migration 0015_auto_20171031_2020.py
    dictionary_entry = models.ForeignKey(DictionaryEntry, on_delete=models.CASCADE, db_constraint=False)

    weight = models.FloatField()
