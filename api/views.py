from rest_framework import viewsets

from searcher.queries import search_entries
from .serializers import DictionaryEntrySerializer

class DictionaryEntryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DictionaryEntrySerializer

    def get_queryset(self):
        query = self.request.query_params.get('query', '')
        matching_entries, _, _ = search_entries(query, paginate=False)
        return matching_entries
