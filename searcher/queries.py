import functools
from collections import defaultdict, Counter

from django.core.paginator import (
    EmptyPage,
    PageNotAnInteger,
    Paginator,
)
from django.db.models import (
    Count,
    F,
    IntegerField,
    Sum,
    Value,
)
from mongoengine.queryset import QuerySet

from importer.models import (
    DictionaryEntry,
    InvertedIndexEntry,
)
from importer.util import normalize_query, normalize_word
from . import const

def search_entries(query, paginate=True, page=1):
    query = normalize_query(query)
    if not query:
        search_terms = []
        matching_entries = DictionaryEntry.objects
        matching_entries = matching_entries.order_by('id')
        matching_entry_weights = None
    else:
        search_terms = set(normalize_word(word) for word in query.split(' '))

        results = InvertedIndexEntry.objects.aggregate(
            # Find all matches for each search term
            {
                "$match": {
                    "index_word_text": {
	                "$in": list(search_terms)
                    }
                }
            },
            # Collect matches into a single list
            {
                "$group": {
                    "_id": 0,
                    "matches_list": {"$push": "$matches"}
                }
            },
            {
                "$project": {
                    "all_matches": {
	                "$reduce": {
	                    "input": "$matches_list",
	                    "initialValue": [],
	                    "in": {"$concatArrays": ["$$value", "$$this"]}
	                }
                    }
                }
            },
            {
                "$unwind": "$all_matches"
            },
            # Sum counts and weights
            {
                "$group": {
                    "_id": "$all_matches.dictionary_entry",
                    "count": {"$sum": 1},
                    "weight": {"$sum": "$all_matches.weight"}
                }
            },
            # Find matches that match all search terms
            {
                "$match": {
                    "count": len(search_terms)
                }
            },
            # Sort by weight (descending)
            {
                "$sort": {
                    "weight": -1
                }
            }
        )

        matching_entry_ids = []
        matching_entry_weights = {}
        for result in results:
            matching_entry_ids.append(result['_id'])
            matching_entry_weights[result['_id']] = result['weight']

        matching_entries = DictionaryEntry.objects.\
                           filter(id__in=matching_entry_ids)

    if paginate:
        paginator = Paginator(matching_entries, per_page=const.RESULTS_PER_PAGE)
        try:
            matching_entries = paginator.page(page)
        except (EmptyPage, PageNotAnInteger):
            matching_entries = []

        total_matches = paginator.count
    else:
        total_matches = matching_entries.count

    if matching_entry_weights:
        for matching_entry in matching_entries:
            matching_entry.weight = matching_entry_weights[matching_entry.id]

    return matching_entries, search_terms, total_matches
