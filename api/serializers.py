from rest_framework_mongoengine import serializers

from importer.models import DictionaryEntry

class DictionaryEntrySerializer(serializers.DocumentSerializer):
    class Meta:
        model = DictionaryEntry
        fields = ('id', 'jp_text', 'en_text',)
