from django.core.paginator import (
    EmptyPage,
    Paginator,
)
from django.db.models import (
    Count,
    F,
    IntegerField,
    Sum,
    Value,
)
from django.http import Http404

from importer.models import (
    DictionaryEntry,
    InvertedIndexEntry,
)
from importer.util import normalize_query, normalize_word
from . import const

def get_entry_by_sequence_number(sequence_number):
    try:
        matching_entries = [
            DictionaryEntry.objects.get(
                sequence_number=sequence_number,
            )
        ]
    except DictionaryEntry.DoesNotExist:
        raise Http404

    paginator = Paginator(matching_entries, per_page=1)

    return paginator.page(1)

def search_entries(query, page=1):
    try:
        page = max(int(page), 1)
    except (TypeError, ValueError):
        page = 1

    query = normalize_query(query)
    if not query:
        total_matches = DictionaryEntry.objects.count()

        matching_entries = DictionaryEntry.objects.\
                           order_by('-common', 'frequency_rank', 'id')

        search_terms = []
    else:
        search_terms = set(normalize_word(word) for word in query.split(' '))

        matching_entries = DictionaryEntry.objects.\
                           filter(invertedindexentry__index_word_text__in=search_terms).\
                           annotate(weight=Sum('invertedindexentry__weight')).\
                           annotate(terms_matched=Count('invertedindexentry__index_word_text', distinct=True)).\
                           filter(terms_matched=len(search_terms)).\
                           order_by('-weight', 'id')

    # Wrap results with Django's Paginator
    paginator = Paginator(matching_entries, per_page=const.RESULTS_PER_PAGE)
    try:
        matching_entries = paginator.page(page)
    except EmptyPage:
        matching_entries = paginator.page(paginator.num_pages)

    total_matches = paginator.count

    return matching_entries, search_terms, total_matches
