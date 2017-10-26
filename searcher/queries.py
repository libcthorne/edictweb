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
    InvertedIndexWord,
)

def paginated_search(query, page=None):
    # Find relevant entries
    query = InvertedIndexWord.normalize_query(query)
    if not query:
        matching_entries = DictionaryEntry.objects.all()
        matching_entries = matching_entries.\
                           annotate(num_matches=Value(0, IntegerField())).\
                           order_by('id')

    else:
        normalized_words = [InvertedIndexWord.normalize_word(word) for word in query.split(' ')]
        matching_entries = DictionaryEntry.objects.filter(invertedindexentry__index_word__word__in=normalized_words).\
                           annotate(num_matches=Count('id')).\
                           order_by('-num_matches', 'id')

    # Paginate results
    paginator = Paginator(matching_entries, per_page=20)
    try:
        paginated_matching_entries = paginator.page(page)
    except PageNotAnInteger:
        paginated_matching_entries = paginator.page(1)
    except EmptyPage:
        paginated_matching_entries = paginator.page(paginator.num_pages)

    total_matches = paginator.count

    if query:
        # Highlight text match positions

        match_positions = InvertedIndexEntry.objects.\
                          filter(index_word__word__in=normalized_words).\
                          filter(dictionary_entry__in=paginated_matching_entries).\
                          order_by('dictionary_entry_id', 'start_position', 'end_position').\
                          annotate(word=F('index_word__word'))

        match_positions_for_entry = defaultdict(list)
        for match_position in match_positions:
            match_positions_for_entry[match_position.dictionary_entry_id].append({
                'word': match_position.word,
                'start_position': match_position.start_position,
                'end_position': match_position.end_position,
            })

        for matching_entry in paginated_matching_entries:
            matching_entry.edict_data_highlighted = []
            prev_match_end = 0

            for match_position in match_positions_for_entry[matching_entry.id]:
                match_start = match_position['start_position']
                match_end = match_position['end_position']

                # Everything from last match to current match start is not highlighted
                matching_entry.edict_data_highlighted.append((
                    False,
                    matching_entry.edict_data[prev_match_end:match_start],
                ))
                # Current match is highlighted
                matching_entry.edict_data_highlighted.append((
                    True,
                    matching_entry.edict_data[match_start:match_end],
                ))

                prev_match_end = match_end

            # Any remaining text after last match is not highlighted
            data_end = len(matching_entry.edict_data)
            if prev_match_end < data_end:
                matching_entry.edict_data_highlighted.append((
                    False,
                    matching_entry.edict_data[prev_match_end:data_end],
                ))

    return {
        'matches_all_entries': bool(not query),
        'paginated_matching_entries': paginated_matching_entries,
        'total_matches': total_matches,
    }
