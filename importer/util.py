import re
import string
import unicodedata

META_INFO_TO_LABEL_MAP = {
    "n": "noun",
    "n-pref": "noun prefix",
    "uk": "usually kana",
    "comp": "computer term",
}

def normalize_query(query):
    return re.sub(r'[;/()\[\[]', ' ', query)

def normalize_word(word):
    # strip trailing whitespace
    word = word.rstrip()
    # make case-insensitive
    word = word.lower()
    # normalize for full-width to half-width conversion, among other things
    word = unicodedata.normalize('NFKC', word)
    # remove punctuation characters
    word = ''.join(c for c in word if c not in string.punctuation)

    return word

def meta_info_to_label(meta_info):
    return META_INFO_TO_LABEL_MAP.get(meta_info, meta_info)
