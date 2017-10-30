from django.shortcuts import render
from rest_framework import viewsets

from importer.models import DictionaryEntry
from .serializers import DictionaryEntrySerializer


class DictionaryEntryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DictionaryEntry.objects.all()
    serializer_class = DictionaryEntrySerializer
