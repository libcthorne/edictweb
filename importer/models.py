import re

from django.db import models
from mongoengine import (
    connect,
    Document,
    EmbeddedDocument,
    fields as mongo_fields,
)

from . import const
from .util import meta_info_to_label

db_conn = connect('dictionary_index')

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

class DictionaryEntry(Document):
    jp_text = mongo_fields.StringField(max_length=2048)
    en_text = mongo_fields.StringField(max_length=2048)
    meta_text = mongo_fields.StringField(max_length=2048)
    sequence_number = mongo_fields.IntField(min_value=0)
    frequency_rank = mongo_fields.IntField(min_value=0)
    common = mongo_fields.BooleanField()
    import_request_id = mongo_fields.IntField(min_value=0)
    meta = {
        'indexes': [
            'sequence_number',
            ('-common', '+frequency_rank', '+_id'),
        ]
    }

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

class DictionaryEntryMatch(EmbeddedDocument):
    dictionary_entry = mongo_fields.ReferenceField(DictionaryEntry)
    weight = mongo_fields.FloatField(min_value=0)

class InvertedIndexEntry(Document):
    index_word_text = mongo_fields.StringField(max_length=256)
    matches = mongo_fields.EmbeddedDocumentListField(DictionaryEntryMatch)
    import_request_id = mongo_fields.IntField(min_value=0)
    meta = {
        'indexes': [
            ('index_word_text', 'import_request_id'),
        ]
    }
