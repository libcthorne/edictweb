from rest_framework import serializers

from importer.models import DictionaryEntry

class DictionaryEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = DictionaryEntry
        fields = ('id', 'jp_text', 'en_text',)
