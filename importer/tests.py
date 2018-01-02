from django.test import TestCase

from .models import (
    DictionaryEntry,
    DictionaryImportRequest,
)
from .util import meta_info_to_label

def create_stub_import_request():
    return DictionaryImportRequest.objects.create(
        started=True,
        completed=True,
    )

class DictionaryEntryTests(TestCase):
    def test_meta_labels(self):
        entry = DictionaryEntry.objects.create(
            jp_text="犬",
            en_text="dog",
            meta_text="n;uk;animal",
            sequence_number=100,
            source_import_request=create_stub_import_request(),
        )

        self.assertCountEqual(entry.meta_labels, [
            meta_info_to_label('n'),
            meta_info_to_label('uk'),
            meta_info_to_label('animal'),
        ])

    def test_str(self):
        entry = DictionaryEntry.objects.create(
            jp_text="犬",
            en_text="dog",
            meta_text="n",
            sequence_number=100,
            source_import_request=create_stub_import_request(),
        )

        self.assertEqual(str(entry), "犬|dog")
