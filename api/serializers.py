from rest_framework import serializers

from importer.models import DictionaryEntry

class DictionaryEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = DictionaryEntry
        fields = ('sequence_number', 'jp_text', 'en_text',)
