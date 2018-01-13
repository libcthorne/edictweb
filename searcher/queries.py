import functools
from collections import defaultdict, Counter, OrderedDict

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
from mongoengine.queryset import QuerySet

from importer.models import (
    DictionaryEntry,
    InvertedIndexEntry,
)
from importer.util import normalize_query, normalize_word
from . import const

class PartialDocumentCollection:
    def __init__(self, documents, offset, count):
        self._documents = documents
        self._offset = offset
        self._count = count

    def __getitem__(self, item):
        if isinstance(item, slice):
            item = slice(item.start-self._offset, item.stop-self._offset)
        else:
            item -= self._offset

        return self._documents[item]

    def __len__(self):
        return count

    def count(self):
        return self._count

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

    limit = const.RESULTS_PER_PAGE
    skip = (page-1)*limit

    query = normalize_query(query)
    if not query:
        total_matches = DictionaryEntry.objects.count()

        matching_entries = list(
            DictionaryEntry.objects.\
            order_by('id').\
            skip(skip).\
            limit(limit)
        )

        search_terms = []
        matching_entry_weights = None
    else:
        search_terms = set(normalize_word(word) for word in query.split(' '))

        base_aggregation = [
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
        ]
        lookup_aggregation = [
            # Only keep weight and _id
            {
                "$project": {
                    "weight": 1
                }
            },
            # Sort by weight (descending)
            {
                # Use OrderedDict to ensure
                # weight is primary sorting key
                "$sort": OrderedDict([
                    ("weight", -1),
                    ("_id", 1),
                ])
            },
            # Paginate
            {
                "$skip": skip
            },
            {
                "$limit": limit
            },
            # Lookup matching entry documents
            {
                "$lookup": {
                    "from": "dictionary_entry",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "dictionary_entry"
                }
            },
            {
                "$unwind": "$dictionary_entry"
            },
        ]
        count_aggregation = [
            {
                "$group": {
                    "_id": "$all_matches.dictionary_entry",
                    "count": {"$sum": 1}
                }
            }
        ]
        results = InvertedIndexEntry.objects.aggregate(
            *(base_aggregation + lookup_aggregation)
        )
        try:
            total_matches = next(InvertedIndexEntry.objects.aggregate(
                *(base_aggregation + count_aggregation)
            ))['count']
        except StopIteration:
            total_matches = 0

        matching_entries = []
        matching_entry_weights = {}
        for result in results:
            result['dictionary_entry']['id'] = result['_id']
            del result['dictionary_entry']['_id']
            matching_entries.append(
                DictionaryEntry(**result['dictionary_entry'])
            )
            matching_entry_weights[result['_id']] = result['weight']

    # Wrap list with Django's Paginator
    matching_entries = PartialDocumentCollection(matching_entries, skip, total_matches)
    paginator = Paginator(matching_entries, per_page=const.RESULTS_PER_PAGE)
    try:
        matching_entries = paginator.page(page)
    except EmptyPage:
        matching_entries = paginator.page(paginator.num_pages)

    if matching_entry_weights:
        for matching_entry in matching_entries:
            matching_entry.weight = matching_entry_weights[matching_entry.id]

    return matching_entries, search_terms, total_matches
