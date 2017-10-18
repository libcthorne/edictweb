from django.db import models

class DictionaryEntry(models.Model):
    edict_data = models.CharField(max_length=2048)

    def __str__(self):
        return self.edict_data

class DictionaryImportRequest(models.Model):
    started = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    interrupted = models.BooleanField(default=False)
    total_entries_count = models.PositiveIntegerField(default=0)
