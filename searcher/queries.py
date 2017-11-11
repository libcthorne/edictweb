from collections import defaultdict

from django.core.paginator import (
    EmptyPage,
    PageNotAnInteger,
    Paginator,
)
from django.db.models import (
    Count,
    F,
    IntegerField,
    Value,
)

from importer.models import (
    DictionaryEntry,
    InvertedIndexEntry,
)

def search_entries(query, paginate=True, page=None):
    query = InvertedIndexEntry.normalize_query(query)
    if not query:
        search_terms = []
        matching_entries = DictionaryEntry.objects.all()
        matching_entries = matching_entries.\
                           annotate(num_matches=Value(0, IntegerField())).\
                           order_by('id')

    else:
        search_terms = [InvertedIndexEntry.normalize_word(word) for word in query.split(' ')]
        matching_entries = DictionaryEntry.objects.filter(invertedindexentry__index_word_text__in=search_terms).\
                           annotate(num_matches=Count('id')).\
                           order_by('-num_matches', 'id')

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

def get_matching_entries_data_highlighted(matching_entries, search_terms):
    matching_entries_data_highlighted = defaultdict(list)

    match_positions = InvertedIndexEntry.objects.\
                      filter(index_word_text__in=search_terms).\
                      filter(dictionary_entry__in=matching_entries).\
                      order_by('dictionary_entry_id', 'start_position', 'end_position').\
                      annotate(word=F('index_word_text'))

    match_positions_for_entry = defaultdict(list)
    for match_position in match_positions:
        match_positions_for_entry[match_position.dictionary_entry_id].append({
            'word': match_position.word,
            'start_position': match_position.start_position,
            'end_position': match_position.end_position,
        })

    for matching_entry in matching_entries:
        prev_match_end = 0

        for match_position in match_positions_for_entry[matching_entry.id]:
            match_start = match_position['start_position']
            match_end = match_position['end_position']

            # Everything from last match to current match start is not highlighted
            matching_entries_data_highlighted[matching_entry].append((
                False,
                matching_entry.edict_data[prev_match_end:match_start],
            ))
            # Current match is highlighted
            matching_entries_data_highlighted[matching_entry].append((
                True,
                matching_entry.edict_data[match_start:match_end],
            ))

            prev_match_end = match_end

        # Any remaining text after last match is not highlighted
        data_end = len(matching_entry.edict_data)
        if prev_match_end < data_end:
            matching_entries_data_highlighted[matching_entry].append((
                False,
                matching_entry.edict_data[prev_match_end:data_end],
            ))

    return matching_entries_data_highlighted
