import re

from django.db import models

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

    # Foreign key constraint with ON DELETE CASCADE manually set
    # See migration 0015_auto_20171031_2020.py
    source_import_request = models.ForeignKey(DictionaryImportRequest, on_delete=models.CASCADE, db_constraint=False)

    @property
    def meta_labels(self):
        meta_labels = []
        meta_text_stripped = re.sub("[\(\){}]", "", self.meta_text)
        meta_text_groups = meta_text_stripped.split(" ")
        for meta_text_group in meta_text_groups:
            meta_infos = meta_text_group.split(",")
            for meta_info in meta_infos:
                meta_labels.append(meta_info_to_label(meta_info))
        return meta_labels

    def __str__(self):
        return self.jp_text + "|" + self.en_text

class InvertedIndexEntry(models.Model):
    index_word_text = models.CharField(max_length=128, db_index=True)

    # Foreign key constraint with ON DELETE CASCADE manually set
    # See migration 0015_auto_20171031_2020.py
    dictionary_entry = models.ForeignKey(DictionaryEntry, on_delete=models.CASCADE, db_constraint=False)

    start_position = models.PositiveIntegerField()
    end_position = models.PositiveIntegerField()

    weight = models.FloatField()

    index_column = models.CharField(max_length=128)

    def __str__(self):
        return "Index of '{}' for {} on column {}".format(
            self.index_word_text,
            self.dictionary_entry,
            self.index_column,
        )
