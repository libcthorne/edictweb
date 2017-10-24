import string
import unicodedata

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    source_import_request = models.ForeignKey(DictionaryImportRequest, on_delete=models.CASCADE)

    def __str__(self):
        return self.edict_data

@receiver(post_save, sender=DictionaryEntry)
def post_save(sender, instance, **kwargs):
    edict_data = InvertedIndexWord.normalize_query(str(instance.edict_data))

    # Index entry words
    for word in edict_data.split(' '):
        start_position = edict_data.index(word)
        word = InvertedIndexWord.normalize_word(word)
        if not word:
            continue # word is not indexable

        # Index each edge n-gram (i.e. quick -> q, qu, qui, quic, quick)
        for i in range(len(word)):
            word_ngram = word[:i+1]
            print("Indexing %s under %s (start:%d)" % (edict_data, word_ngram, start_position))
            inverted_index_word, _ = InvertedIndexWord.objects.get_or_create(word=word_ngram)
            inverted_index_entry = InvertedIndexEntry(
                index_word=inverted_index_word,
                dictionary_entry=instance,
                start_position=start_position,
            )
            inverted_index_entry.save()

class InvertedIndexWord(models.Model):
    word = models.CharField(max_length=128)

    @staticmethod
    def normalize_query(query):
        return query.replace(';', ' ').replace('/', ' ')

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
        return self.word

class InvertedIndexEntry(models.Model):
    index_word = models.ForeignKey(InvertedIndexWord, on_delete=models.CASCADE, related_name='entries')
    dictionary_entry = models.ForeignKey(DictionaryEntry, on_delete=models.CASCADE)
    start_position = models.PositiveIntegerField()

    def __str__(self):
        return "Index of '{}' for {}".format(self.index_word, self.dictionary_entry)
