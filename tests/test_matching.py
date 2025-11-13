import pytest
import pandas as pd
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from app.matching import Matcher

@pytest.fixture(scope="module")
def sample_matcher():
    """Fixture for a simple matcher with basic ingredients."""
    data = {
        'ingredient_id': ['1', '2', '3', '6', '8', '9'], 
        'name': ['Tomato', 'Onion', 'Garlic', 'Cumin Seeds', 'All-Purpose Flour', 'Unsalted Butter']
    }
    df = pd.DataFrame(data)
    return Matcher(df)

def test_matcher_init(sample_matcher):
    assert not sample_matcher.master_data.empty
    assert 'normalized_name' in sample_matcher.master_data.columns
    assert 'tomato' in sample_matcher.index
    assert sample_matcher.index['tomato'] == {'1'}

def test_exact_match(sample_matcher):
    id, conf = sample_matcher.match("Tomato", 70)
    assert id == '1'
    assert conf == 1.0

def test_fuzzy_match_plural(sample_matcher):
    id, conf = sample_matcher.match("Tomatoes", 70)
    assert id == '1'
    assert conf > 0.9  # 'tomatoes' -> 'tomato' via SYNONYM_MAP

def test_fuzzy_match_misspelling(sample_matcher):
    # 'gralic' -> 'garlic' via SYNONYM_MAP
    id, conf = sample_matcher.match("Gralic", 70)
    assert id == '3'
    assert conf == 1.0

def test_match_with_noise(sample_matcher):
    id, conf = sample_matcher.match("peeled garlic 100g pack", 70)
    assert id == '3'
    assert conf == 1.0

def test_synonym_match_jeera(sample_matcher):
    # 'jeera' -> 'cumin' via SYNONYM_MAP
    id, conf = sample_matcher.match("jeera seeds 50g", 70)
    assert id == '6'
    assert conf == 1.0

def test_synonym_match_flour(sample_matcher):
    # 'plain flour' -> 'all-purpose flour' via SYNONYM_MAP
    id, conf = sample_matcher.match("plain flour 1kg", 70)
    assert id == '8'
    assert conf == 1.0

def test_synonym_match_butter(sample_matcher):
    # 'unslt' -> 'unsalted' via SYNONYM_MAP
    id, conf = sample_matcher.match("unslt butter", 70)
    assert id == '9'
    assert conf == 1.0

def test_no_good_match(sample_matcher):
    # Should return the *best* available match, even if bad
    id, conf = sample_matcher.match("Broccoli", 70)
    assert id is not None  # Should still find a *best* match
    assert conf < 0.7      # Confidence should be low

def test_empty_query(sample_matcher):
    id, conf = sample_matcher.match("", 70)
    assert id is None
    assert conf == 0.0

def test_none_query(sample_matcher):
    id, conf = sample_matcher.match(None, 70)
    assert id is None
    assert conf == 0.0

def test_token_blocking(sample_matcher):
    # This test ensures we're not brute-forcing
    # 'Gralic' -> 'garlic', should only check candidate '3'
    candidates = sample_matcher._get_candidates("garlic")
    assert candidates == {'3'}

def test_blocking_fallback(sample_matcher):
    # 'zzzz' matches no tokens, should fall back to all candidates
    all_ids = set(sample_matcher.master_data['ingredient_id'])
    candidates = sample_matcher._get_candidates("zzzz")
    assert candidates == all_ids