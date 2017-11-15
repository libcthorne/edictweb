from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response

from importer.models import DictionaryEntry
from searcher.queries import search_entries
from .serializers import DictionaryEntrySerializer

class DictionaryEntryList(APIView):
    def get(self, request, format=None):
        query = request.query_params.get('query', None)
        if query:
            matching_entries, _, _ = search_entries(query, paginate=False)
        else:
            matching_entries = DictionaryEntry.objects.all()

        serializer = DictionaryEntrySerializer(matching_entries, many=True)
        return Response(serializer.data)
