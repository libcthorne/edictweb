from django.db import models

class DictionaryEntry(models.Model):
    edict_data = models.CharField(max_length=256)

    def __str__(self):
        return self.edict_data

class DictionaryImportRequest(models.Model):
    completed = models.BooleanField(default=False)
