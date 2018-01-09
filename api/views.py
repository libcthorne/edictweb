from rest_framework.response import Response
from rest_framework.views import APIView

from importer.models import DictionaryEntry
from searcher.queries import search_entries
from .serializers import DictionaryEntrySerializer

class DictionaryEntryList(APIView):
    def get(self, request, format=None):
        query = request.query_params.get('query', '')
        page = request.query_params.get('page', 1)
        matching_entries, _, total_matches = search_entries(query, page=page)

        serializer = DictionaryEntrySerializer(matching_entries, many=True)
        return Response({
            'count': total_matches,
            'results': serializer.data,
            'has_next': matching_entries.has_next(),
        })
