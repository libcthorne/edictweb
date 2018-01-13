from importer import const, util

def get_text_highlighted(text, description_separator, search_terms):
    text_highlighted = []
    descriptions = text.split(description_separator)

    for description_index, description in enumerate(descriptions):
        words = description.split(const.DESCRIPTION_WORD_SEPARATOR)

        for word_index, word in enumerate(words):
            match_found = False

            normalized_word = util.normalize_word(word)
            if normalized_word:
                for search_term in search_terms:
                    match_start = normalized_word.lower().find(search_term)
                    if match_start == 0:
                        match_found = True
                        break

            if match_found:
                # Highlight word
                text_highlighted.append((True, word))
            else:
                # No match, don't highlight word
                text_highlighted.append((False, word))

            if word_index+1 < len(words):
                # Don't highlight word separator
                text_highlighted.append((False, const.DESCRIPTION_WORD_SEPARATOR))

        if description_index+1 < len(descriptions):
            # Don't highlight description separator
            text_highlighted.append((False, description_separator))

    return text_highlighted
