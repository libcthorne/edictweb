from django.test import TestCase
from django.urls import reverse

from importer.models import (
    DictionaryEntry,
    DictionaryEntryMatch,
    InvertedIndexEntry,
)

def create_dog_dictionary_entry():
    return DictionaryEntry.objects.create(
        jp_text="犬",
        en_text="dog",
        meta_text="(n) (uk) {animal}",
        sequence_number=100,
    )

def create_cat_dictionary_entry():
    return DictionaryEntry.objects.create(
        jp_text="猫",
        en_text="cat",
        meta_text="(n) {animal}",
        sequence_number=101,
    )

class SearchViewTests(TestCase):
    def test_index_with_no_dictionary_entries(self):
        response = self.client.get(reverse("searcher:index"))
        self.assertEqual(response.status_code, 200)

        c = response.context
        self.assertEqual(c['should_highlight'], False)
        self.assertEqual(c['total_matches'], 0)

    def test_index_with_dictionary_entries(self):
        entry1 = create_dog_dictionary_entry()
        entry2 = create_cat_dictionary_entry()

        response = self.client.get(reverse("searcher:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "猫")
        self.assertContains(response, "犬")

        c = response.context
        self.assertEqual(c['should_highlight'], False)
        self.assertEqual(c['total_matches'], 2)

    def test_invalid_sequence_lookup(self):
        response = self.client.get(reverse("searcher:index"), {'seq_no': 100})
        self.assertEqual(response.status_code, 404)

    def test_valid_sequence_lookup(self):
        entry1 = create_dog_dictionary_entry()
        entry2 = create_cat_dictionary_entry()

        response = self.client.get(reverse("searcher:index"), {'seq_no': 100})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "犬")
        self.assertNotContains(response, "猫")

        c = response.context
        self.assertEqual(c['should_highlight'], False)
        self.assertEqual(c['total_matches'], 1)

    def test_empty_query(self):
        entry1 = create_dog_dictionary_entry()
        entry2 = create_cat_dictionary_entry()

        response = self.client.get(reverse("searcher:index"), {'query': ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "犬")
        self.assertContains(response, "猫")

        c = response.context
        self.assertEqual(c['should_highlight'], False)
        self.assertEqual(c['total_matches'], 2)

    def test_valid_query(self):
        entry1 = create_dog_dictionary_entry()
        entry2 = create_cat_dictionary_entry()

        InvertedIndexEntry.objects.create(
            index_word_text="dog",
            matches=[
                DictionaryEntryMatch(
                    dictionary_entry=entry1,
                    weight=0.5,
                )
            ]
        )

        InvertedIndexEntry.objects.create(
            index_word_text="cat",
            matches=[
                DictionaryEntryMatch(
                    dictionary_entry=entry2,
                    weight=0.5,
                )
            ]
        )

        response = self.client.get(reverse("searcher:index"), {'query': "dog"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "犬")
        self.assertNotContains(response, "猫")

        c = response.context
        self.assertEqual(c['should_highlight'], True)
        self.assertEqual(c['total_matches'], 1)

    def test_post_redirect(self):
        response = self.client.post(reverse("searcher:index"), {'query': "dog"}, follow=True)
        self.assertEqual(response.status_code, 200)
