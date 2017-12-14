from django.test import TestCase
from django.urls import reverse

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

    def test_empty_query(self):
        import_request = create_stub_import_request()

        entry1 = create_dog_dictionary_entry(import_request)
        entry2 = create_cat_dictionary_entry(import_request)

        response = self.client.get(reverse("searcher:index"), {'query': ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "犬")
        self.assertContains(response, "猫")

    def test_valid_query(self):
        import_request = create_stub_import_request()

        entry1 = create_dog_dictionary_entry(import_request)
        entry2 = create_cat_dictionary_entry(import_request)

        InvertedIndexEntry.objects.create(
            index_word_text="dog",
            dictionary_entry=entry1,
            start_position=0,
            end_position=3,
            weight=0.5,
            index_column='en_text',
        )

        InvertedIndexEntry.objects.create(
            index_word_text="cat",
            dictionary_entry=entry2,
            start_position=0,
            end_position=3,
            weight=0.5,
            index_column='en_text',
        )

        response = self.client.get(reverse("searcher:index"), {'query': "dog"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "犬")
        self.assertNotContains(response, "猫")

    def test_post_redirect(self):
        response = self.client.post(reverse("searcher:index"), {'query': "dog"}, follow=True)
        self.assertEqual(response.status_code, 200)
