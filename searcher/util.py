from collections import defaultdict

from importer import const

def get_matching_entries_data_highlighted(matching_entries, search_terms, index_column, description_separator):
    matching_entries_data_highlighted = defaultdict(list)

    for matching_entry in matching_entries:
        text = getattr(matching_entry, index_column)
        descriptions = text.split(description_separator)

        for description_index, description in enumerate(descriptions):
            words = description.split(const.DESCRIPTION_WORD_SEPARATOR)

            for word_index, word in enumerate(words):
                longest_match = 0
                for search_term in search_terms:
                    match_start = word.lower().find(search_term)
                    if match_start != 0:
                        # only check matches starting from first character
                        # because these are what are indexed
                        continue

                    longest_match = max(longest_match, len(search_term))

                if longest_match > 0:
                    matching_entries_data_highlighted[matching_entry].append((
                        True, word[:longest_match]
                    ))
                    if longest_match < len(word):
                        matching_entries_data_highlighted[matching_entry].append((
                            False, word[longest_match:]
                        ))
                else:
                    matching_entries_data_highlighted[matching_entry].append((
                        False, word
                    ))

                if word_index+1 < len(words):
                    matching_entries_data_highlighted[matching_entry].append((
                        False, const.DESCRIPTION_WORD_SEPARATOR
                    ))

            if description_index+1 < len(descriptions):
                matching_entries_data_highlighted[matching_entry].append((
                    False, description_separator
                ))

    return matching_entries_data_highlighted
