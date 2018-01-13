from rest_framework_mongoengine import serializers

from importer.models import DictionaryEntry

class DictionaryEntrySerializer(serializers.DocumentSerializer):
    class Meta:
        model = DictionaryEntry
        fields = ('sequence_number', 'jp_text', 'en_text',)
