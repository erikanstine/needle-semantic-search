import pytest
from scraper.utils.text_util import (
    split_sentences,
    generate_snippet,
    is_filler_sentence,
    generate_snippets,
    FILLER_PREFIXES,
)


def test_split_sentences_basic():
    text = "Hello world! How are you? I'm fine."
    expected = ["Hello world!", "How are you?", "I'm fine."]
    assert split_sentences(text) == expected


def test_split_sentences_with_abbreviations():
    text = "Dr. Smith went to Washington. He arrived at 5 p.m. It was late."
    expected = ["Dr. Smith went to Washington.", "He arrived at 5 p.m.", "It was late."]
    assert split_sentences(text) == expected


def test_split_sentences_empty():
    assert split_sentences("") == []


def test_split_sentences_no_punctuation():
    text = "This is a test without punctuation"
    expected = ["This is a test without punctuation"]
    assert split_sentences(text) == expected


def test_generate_snippet_basic():
    text = "Hello world! How are you? I'm fine."
    snippet = generate_snippet(text, max_chars=50)
    assert snippet == "Hello world! How are you? I'm fine."


def test_generate_snippet_respects_max_chars():
    text = "Hello world! How are you? I'm fine. This is a test sentence."
    snippet = generate_snippet(text, max_chars=25)
    assert snippet.startswith("Hello world!")


def test_generate_snippet_empty():
    assert generate_snippet("", max_chars=100) == ""


def test_generate_snippet_long_text():
    text = (
        "Sentence one. Sentence two is longer. Sentence three is even longer than sentence two. "
        "Sentence four ends here."
    )
    snippet = generate_snippet(text, max_chars=50)
    assert snippet.startswith("Sentence one.")


# New tests for expanded functionality
def test_split_sentences_filters_fillers():
    text = "Good morning. This is a test. Thanks."
    # "Good morning." and "Thanks." are fillers and should be removed
    assert split_sentences(text) == ["This is a test."]


def test_is_filler_sentence_true():
    for phrase in FILLER_PREFIXES:
        # exact match
        assert is_filler_sentence(phrase)
        # with punctuation
        assert is_filler_sentence(phrase.capitalize() + ".")
        # with a name suffix
        assert is_filler_sentence(f"{phrase}, John")


def test_is_filler_sentence_false():
    assert not is_filler_sentence("This is not filler.")
    # similar but not exact or prefix-with-comma
    assert not is_filler_sentence("Good morning everyone!")


def test_generate_snippets_basic():
    texts = ["Hello world! How are you?"]
    snippets = generate_snippets(texts, max_chars=50, context=1)
    assert snippets == ["Hello world! How are you?"]


def test_generate_snippet_with_query_and_context():
    text = "First. Second. Third. Fourth."
    snippet = generate_snippet(text, max_chars=100, query="Third", context=1)
    # Should include the sentence before and after the match, joined with ellipses
    assert "Second" in snippet and "Third" in snippet and "Fourth" in snippet
    assert "..." in snippet
