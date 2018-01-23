from django.test import TestCase
from django.urls import reverse

from edictweb import settings
from importer.models import (
    DictionaryEntry,
    DictionaryImportRequest,
    InvertedIndexEntry,
)

def create_stub_import_request():
    return DictionaryImportRequest.objects.create(
        started=True,
        completed=True,
    )

def create_dog_dictionary_entry():
    return DictionaryEntry.objects.create(
        jp_text="犬",
        en_text="dog",
        meta_text="n;uk;animal",
        common=False,
        sequence_number=100,
        source_import_request=create_stub_import_request(),
    )

def create_cat_dictionary_entry():
    return DictionaryEntry.objects.create(
        jp_text="猫",
        en_text="cat",
        meta_text="n;animal",
        common=True,
        sequence_number=101,
        source_import_request=create_stub_import_request(),
    )

class APISearchViewTests(TestCase):
    def test_index_with_no_dictionary_entries(self):
        response = self.client.get(reverse("api:entries"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "count": 0,
                "has_next": False,
                "results": [],
            },
        )

    def test_index_with_dictionary_entries(self):
        entry1 = create_dog_dictionary_entry()
        entry2 = create_cat_dictionary_entry()

        response = self.client.get(reverse("api:entries"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "count": 2,
                "has_next": False,
                "results": [
                    {
                        "en_text": "cat",
                        "jp_text": "猫",
                        "sequence_number": 101,
                    },
                    {
                        "en_text": "dog",
                        "jp_text": "犬",
                        "sequence_number": 100,
                    },
                ],
            },
        )

    def test_empty_query(self):
        entry1 = create_dog_dictionary_entry()
        entry2 = create_cat_dictionary_entry()

        response = self.client.get(reverse("api:entries"), {'query': ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "count": 2,
                "has_next": False,
                "results": [
                    {
                        "en_text": "cat",
                        "jp_text": "猫",
                        "sequence_number": 101,
                    },
                    {
                        "en_text": "dog",
                        "jp_text": "犬",
                        "sequence_number": 100,
                    },
                ],
            },
        )

    def test_valid_query(self):
        entry1 = create_dog_dictionary_entry()
        entry2 = create_cat_dictionary_entry()

        InvertedIndexEntry.objects.create(
            index_word_text="dog",
            dictionary_entry=entry1,
            weight=0.5,
        )

        InvertedIndexEntry.objects.create(
            index_word_text="cat",
            dictionary_entry=entry2,
            weight=0.5,
        )

        response = self.client.get(reverse("api:entries"), {'query': "dog"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "count": 1,
                "has_next": False,
                "results": [
                    {
                        "en_text": "dog",
                        "jp_text": "犬",
                        "sequence_number": 100,
                    },
                ],
            },
        )
