import os
import re

from edictweb.settings import BASE_DIR

# Path to save uploaded dictionary files
DICTIONARY_FILE = os.path.join(BASE_DIR, "JMdict_e")

# Pattern to match nf01, nf02, etc.
FREQUENCY_STRING_REGEX = re.compile("nf[0-9][0-9]")

# e.g. 〃;おなじ;おなじく
JP_TEXT_DESCRIPTION_SEPARATOR = ";"

# e.g. to total/to sum
EN_TEXT_DESCRIPTION_SEPARATOR = "/"

# e.g. noun;verb
META_TEXT_SEPARATOR = ";"

# e.g. to total
DESCRIPTION_WORD_SEPARATOR = " "

# Largest rank value for a dictionary entry
MAX_FREQUENCY_RANK = 50
