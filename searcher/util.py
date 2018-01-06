from importer import const

def get_text_highlighted(text, description_separator, search_terms):
    highlight_info = []
    descriptions = text.split(description_separator)

    for description_index, description in enumerate(descriptions):
        words = description.split(const.DESCRIPTION_WORD_SEPARATOR)

        for word_index, word in enumerate(words):
            longest_match = 0

            for search_term in search_terms:
                match_start = word.lower().find(search_term)

                if match_start != 0:
                    # Only check matches starting from first character
                    # because these are all that are indexed
                    continue

                longest_match = max(longest_match, len(search_term))

            if longest_match > 0:
                # Highlight word up until end of longest match
                highlight_info.append((True, word[:longest_match]))

                if longest_match < len(word):
                    # Don't highlight remainder of word for partial matches
                    highlight_info.append((False, word[longest_match:]))
            else:
                # No match, don't highlight word
                highlight_info.append((False, word))

            if word_index+1 < len(words):
                # Don't highlight word separator
                highlight_info.append((False, const.DESCRIPTION_WORD_SEPARATOR))

        if description_index+1 < len(descriptions):
            # Don't highlight description separator
            highlight_info.append((False, description_separator))

    return highlight_info
