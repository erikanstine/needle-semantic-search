import pytest
from scraper.utils.text_util import split_sentences, generate_snippet

def test_split_sentences_basic():
    text = "Hello world! How are you? I'm fine."
    expected = ["Hello world!", "How are you?", "I'm fine."]
    assert split_sentences(text) == expected

def test_split_sentences_with_abbreviations():
    text = "Dr. Smith went to Washington. He arrived at 5 p.m. It was late."
    expected = [
        "Dr. Smith went to Washington.",
        "He arrived at 5 p.m.",
        "It was late."
    ]
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

def test_generate_snippet_exact_length():
    text = "Hi! Bye."
    snippet = generate_snippet(text, max_chars=len("Hi! Bye."))
    assert snippet == "Hi! Bye."

def test_generate_snippet_long_text():
    text = ("Sentence one. Sentence two is longer. Sentence three is even longer than sentence two. "
            "Sentence four ends here.")
    snippet = generate_snippet(text, max_chars=50)
    assert snippet.startswith("Sentence one.")