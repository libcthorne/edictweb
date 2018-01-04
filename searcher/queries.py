import functools
from collections import defaultdict, Counter

from django.core.paginator import (
    EmptyPage,
    PageNotAnInteger,
    Paginator,
)
from django.db.models import (
    F,
    IntegerField,
    Max,
    Value,
)

from importer.models import (
    DictionaryEntry,
    InvertedIndexEntry,
)
from importer.util import normalize_query, normalize_word

def search_entries(query, paginate=True, page=None):
    query = normalize_query(query)
    if not query:
        search_terms = []
        matching_entries = DictionaryEntry.objects.all()
        matching_entries = matching_entries.order_by('id')
    else:
        search_terms = [normalize_word(word) for word in query.split(' ')]
        matching_entries = DictionaryEntry.objects.\
                           filter(invertedindexentry__index_word_text__in=search_terms).\
                           annotate(weight=Max('invertedindexentry__weight')).\
                           order_by('-weight', 'id')

    if paginate:
        paginator = Paginator(matching_entries, per_page=20)
        try:
            matching_entries = paginator.page(page)
        except PageNotAnInteger:
            matching_entries = paginator.page(1)
        except EmptyPage:
            matching_entries = paginator.page(paginator.num_pages)

        total_matches = paginator.count
    else:
        total_matches = matching_entries.count

    return matching_entries, search_terms, total_matches
