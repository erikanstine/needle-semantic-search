import re


ABBREVIATIONS = {
    "dr.",
    "mr.",
    "mrs.",
    "ms.",
    "inc.",
    "ltd.",
    "corp.",
    "co.",
    "jan.",
    "feb.",
    "mar.",
    "apr.",
    "jun.",
    "jul.",
    "aug.",
    "sep.",
    "oct.",
    "nov.",
    "dec.",
}


def split_sentences(text: str) -> list[str]:
    if not text.strip():
        return []
    parts = re.split(r"(?<=[.!?]) +", text)
    sentences = []
    current = ""

    for part in parts:
        current += part.strip() + " "
        lower_part = part.lower().strip()
        if not any(
            lower_part.endswith(abbrev) for abbrev in ABBREVIATIONS
        ) and re.search(r"[.!?]$", part.strip()):
            sentences.append(current.strip())
            current = ""

    if current:
        sentences.append(current.strip())

    return sentences


def generate_snippet(text: str, max_chars: int = 300) -> str:

    sentences = split_sentences(text)
    snippet = ""
    for sentence in sentences:
        if len(snippet) + len(sentence) <= max_chars:
            snippet += sentence + " "
        else:
            break

    return snippet.strip()
