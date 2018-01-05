from collections import defaultdict

def get_matching_entries_data_highlighted(matching_entries, search_terms, index_column):
    description_separator = "/" if index_column == "en_text" else None
    word_separator = " " if index_column == "en_text" else ";"

    matching_entries_data_highlighted = defaultdict(list)

    for matching_entry in matching_entries:
        text = getattr(matching_entry, index_column)
        descriptions = text.split(description_separator) if description_separator else [text]

        for description_index, description in enumerate(descriptions):
            words = description.split(word_separator)

            for word_index, word in enumerate(words):
                longest_match = 0
                for search_term in search_terms:
                    match_start = word.find(search_term)
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
                        False, word_separator
                    ))

            if description_index+1 < len(descriptions):
                matching_entries_data_highlighted[matching_entry].append((
                    False, description_separator
                ))

    return matching_entries_data_highlighted
