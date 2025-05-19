import re
from .candidates import FILLER_PREFIXES


def is_filler_sentence(sentence: str) -> bool:
    """
    Return True if the sentence matches a known filler prefix or exact phrase.
    """
    norm = sentence.strip().rstrip(".!?").lower()
    # exact match
    if norm in FILLER_PREFIXES:
        return True
    # prefix match (e.g., "good morning, greg")
    return any(norm.startswith(prefix + ",") for prefix in FILLER_PREFIXES)


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

    # # Filter out common filler-only sentences
    sentences = [s for s in sentences if not is_filler_sentence(s)]

    return sentences


def generate_snippet(
    text: str,
    max_chars: int = 500,
    query: str | None = None,
    context: int = 1,
) -> str:
    """
    Generate a snippet of up to max_chars characters.
    If query is provided, returns the matching sentence plus up to `context`
    sentences before and after. Otherwise, returns the first batch of
    non-filler sentences up to the character limit.
    """
    sentences = split_sentences(text)
    if query:
        q = query.lower()
        # Find all sentence indices containing the query
        matches = [i for i, s in enumerate(sentences) if q in s.lower()]
        if matches:
            idx = matches[0]
            start = max(idx - context, 0)
            end = min(idx + context + 1, len(sentences))
            snippet_sentences = sentences[start:end]
            snippet = " ... ".join(snippet_sentences)
            # Trim to max_chars, ending on a word boundary
            if len(snippet) > max_chars:
                snippet = snippet[:max_chars].rsplit(" ", 1)[0] + "..."
            return snippet
    # Fallback: take sentences in order until limit. If we cannot include an
    # entire sentence because it would exceed ``max_chars`` we truncate on a
    # word boundary and append an ellipsis so callers know the text was
    # shortened.
    snippet = ""
    truncated = False
    for idx, sentence in enumerate(sentences):
        sep = " " if snippet else ""
        if len(snippet) + len(sep) + len(sentence) <= max_chars:
            snippet += sep + sentence
        else:
            remaining = max_chars - len(snippet) - 3
            if remaining > 0:
                snippet += sep + sentence[:remaining]
                snippet = snippet.rstrip().rsplit(" ", 1)[0]
            truncated = True
            break
    else:
        if idx < len(sentences) - 1:
            truncated = True

    snippet = snippet.strip()
    if truncated:
        if len(snippet) + 3 > max_chars:
            snippet = snippet[: max_chars - 3].rsplit(" ", 1)[0]
        snippet = snippet.rstrip() + "..."
    return snippet


def generate_snippets(
    texts: list[str],
    max_chars: int = 500,
    context: int = 1,
) -> list[str]:
    """
    Generate snippets for each text in `texts` using generate_snippet.
    """
    return [
        generate_snippet(text, max_chars=max_chars, context=context) for text in texts
    ]
