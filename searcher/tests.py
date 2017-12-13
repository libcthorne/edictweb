from django.test import TestCase
from django.urls import reverse

from importer.models import (
    DictionaryEntry,
    DictionaryImportRequest,
)

def create_stub_import_request():
    return DictionaryImportRequest.objects.create(
        started=True,
        completed=True,
    )

def create_dog_dictionary_entry(import_request):
    return DictionaryEntry.objects.create(
        jp_text="犬",
        en_text="dog",
        meta_text="(n) (uk) {animal}",
        sequence_number=100,
        source_import_request=import_request,
    )

def create_cat_dictionary_entry(import_request):
    return DictionaryEntry.objects.create(
        jp_text="猫",
        en_text="cat",
        meta_text="(n) {animal}",
        sequence_number=101,
        source_import_request=import_request,
    )

class SearchViewTests(TestCase):
    def test_index_with_no_dictionary_entries(self):
        response = self.client.get(reverse("searcher:index"))
        self.assertEqual(response.status_code, 200)

    def test_index_with_dictionary_entries(self):
        import_request = create_stub_import_request()

        entry1 = create_dog_dictionary_entry(import_request)
        entry2 = create_cat_dictionary_entry(import_request)

        response = self.client.get(reverse("searcher:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "猫")
        self.assertContains(response, "犬")

    def test_invalid_sequence_lookup(self):
        response = self.client.get(reverse("searcher:index"), {'seq_no': 100})
        self.assertEqual(response.status_code, 404)

    def test_valid_sequence_lookup(self):
        import_request = create_stub_import_request()

        entry1 = create_dog_dictionary_entry(import_request)
        entry2 = create_cat_dictionary_entry(import_request)

        response = self.client.get(reverse("searcher:index"), {'seq_no': 100})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "犬")
        self.assertNotContains(response, "猫")
