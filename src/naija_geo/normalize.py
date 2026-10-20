"""Turn place names into match keys, so spelling variants compare equal.

``normalize("Ifako/Ijaiye") == normalize("ifako-ijaiye") == "ifako ijaiye"``
"""

import re
import unicodedata

# ASCII ', curly quotes U+2019 and U+2018, modifier letter apostrophe U+02BC, backtick
_APOSTROPHES = re.compile("['\u2019\u2018\u02bc`]")
_SEPARATORS = re.compile(r"[\s/_-]+")


def normalize(text: str) -> str:
    """Return the match key for a name.

    Case-folds, strips accents and apostrophes, treats ``-``, ``/``, ``_`` and whitespace
    as one separator, and trims the ends.
    """
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    unaccented = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(_SEPARATORS.split(_APOSTROPHES.sub("", unaccented))).strip()


def normalize_state(text: str) -> str:
    """Return the match key for a state name, ignoring a "State" suffix or "State of" prefix.

    ``normalize_state("Lagos State") == normalize_state("State of Lagos") == "lagos"``
    """
    words = normalize(text).split()
    if words[:2] == ["state", "of"] and len(words) > 2:
        words = words[2:]
    elif words[-1:] == ["state"] and len(words) > 1:
        words = words[:-1]
    return " ".join(words)
