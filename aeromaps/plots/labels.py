"""Readable labels for identifiers coming from the configuration files."""

# Acronyms kept upper case when a snake_case identifier is turned into a label.
_ACRONYMS = {"atm": "ATM", "apu": "APU", "saf": "SAF", "co2": "CO2"}


def readable_label(raw_name):
    """Turn a snake_case identifier into a label: first word capitalised, acronyms upper case."""
    words = [_ACRONYMS.get(word, word) for word in raw_name.split("_")]
    if words and words[0] not in _ACRONYMS.values():
        words[0] = words[0].capitalize()
    return " ".join(words)
