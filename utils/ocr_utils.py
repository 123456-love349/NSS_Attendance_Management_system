import re


def clean_roll(text):

    text = text.upper()

    corrections = {
        "O": "0",
        "I": "1",
        "L": "1",
        "S": "5",
        "B": "8",
        "Z": "2",
        "G": "6"
    }

    cleaned = ""

    for ch in text:

        if ch in corrections:
            cleaned += corrections[ch]
        else:
            cleaned += ch

    cleaned = re.sub(r'[^0-9]', '', cleaned)

    return cleaned


def is_roll(text):

    text = clean_roll(text)

    return len(text) >= 6