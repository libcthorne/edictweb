from collections import defaultdict

def get_matching_entries_data_highlighted(matching_entries, search_terms, index_column):
    matching_entries_data_highlighted = defaultdict(list)
    for matching_entry in matching_entries:
        matching_entries_data_highlighted[matching_entry].append((
            False,
            getattr(matching_entry, index_column),
        ))
    return matching_entries_data_highlighted
