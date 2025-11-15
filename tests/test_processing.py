import pytest
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from app.processing import normalize

def test_lowercase():
    assert normalize("TOMATO") == "tomato"

def test_remove_pack_size_simple():
    assert normalize("tomato 1kg pack") == "tomato"

def test_remove_pack_size_complex():
    assert normalize("flour 2.5 kg bag") == "bag flour"

def test_remove_pack_size_with_decimal():
    assert normalize("olive oil 0.5l bottle") == "olive oil"

def test_punctuation():
    assert normalize("tomato, red!") == "tomato"

def test_stopwords():
    assert normalize("extra virgin olive oil") == "olive oil"

def test_lemmatization():
    assert normalize("tomatoes") == "tomato"

def test_misspelling_and_synonym():
    # 'gralic' -> 'garlic'
    assert normalize("gralic peeled 100 g") == "garlic"

def test_synonym_jeera():
    # 'jeera seeds' -> 'cumin seeds'
    assert normalize("jeera seeds 50g") == "cumin seed"
    assert normalize("Cumin Seeds") == "cumin seed"

def test_synonym_flour():
    # 'plain flour' -> 'all-purpose flour'
    assert normalize("plain flour 1kg") == "all-purpose flour"
    assert normalize("All-Purpose Flour") == "all-purpose flour"

def test_synonym_sugar():
    # 'white sugar' -> 'granulated sugar'
    assert normalize("white sugar 2kg") == "granulated sugar"
    assert normalize("Granulated Sugar") == "granulated sugar"

def test_abbreviation_butter():
    # 'unslt butter' -> 'unsalted butter'
    assert normalize("butter unslt 250 g") == "butter unsalted"
    assert normalize("Unsalted Butter") == "butter unsalted"

def test_sorting_and_uniqueness():
    assert normalize("oil olive virgin extra") == "olive oil"
    assert normalize("tomato tomato tomato") == "tomato"

def test_empty_and_none():
    assert normalize("") == ""
    assert normalize(None) == ""

def test_numbers_only():
    assert normalize("123 456") == ""