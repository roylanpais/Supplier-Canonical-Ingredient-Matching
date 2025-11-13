"""Unit tests for matching engine and preprocessing."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.matcher import FuzzyMatcher
from app.preprocessing import TextPreprocessor


@pytest.fixture
def sample_ingredients():
    """Sample ingredients for testing."""
    return [
        {'ingredient_id': 1, 'name': 'Tomato'},
        {'ingredient_id': 2, 'name': 'Onion'},
        {'ingredient_id': 3, 'name': 'Garlic'},
        {'ingredient_id': 4, 'name': 'Olive Oil'},
        {'ingredient_id': 5, 'name': 'Whole Milk'},
    ]


@pytest.fixture
def matcher(sample_ingredients):
    """Matcher instance with sample data."""
    return FuzzyMatcher(sample_ingredients)


class TestPreprocessing:
    """Tests for text preprocessing."""
    
    def test_normalize_text_lowercase(self):
        result = TextPreprocessor.normalize_text('TOMATO')
        assert result == 'tomato'
    
    def test_normalize_text_removes_units(self):
        result = TextPreprocessor.normalize_text('tomato 1kg')
        assert '1kg' not in result
        assert 'tomato' in result
    
    def test_normalize_text_removes_special_chars(self):
        result = TextPreprocessor.normalize_text('tomato (fresh)')
        assert 'fresh' in result
        assert '(' not in result
    
    def test_tokenize(self):
        tokens = TextPreprocessor.tokenize('tomato red fresh')
        assert 'tomato' in tokens
        assert 'fresh' in tokens
        assert 'red' not in tokens  # stop word
    
    def test_correct_misspellings(self):
        result = TextPreprocessor.correct_misspellings('gralic')
        assert 'garlic' in result
    
    def test_preprocess_full_pipeline(self):
        result = TextPreprocessor.preprocess('GRALIC PEELED 100g')
        assert '100g' not in result


class TestSimilarity:
    """Tests for similarity metrics."""
    
    def test_token_set_similarity_identical(self):
        score = FuzzyMatcher.token_set_similarity('tomato', 'tomato')
        assert score == 1.0
    
    def test_token_set_similarity_partial(self):
        score = FuzzyMatcher.token_set_similarity('fresh tomato', 'tomato red')
        assert 0 < score < 1
    
    def test_token_set_similarity_empty(self):
        score = FuzzyMatcher.token_set_similarity('', '')
        assert score == 1.0
    
    def test_string_similarity_similar(self):
        score = FuzzyMatcher.string_similarity('tomato', 'tomato')
        assert score == 1.0
    
    def test_combined_similarity(self):
        score = FuzzyMatcher.combined_similarity('fresh tomato', 'tomato')
        assert 0 < score <= 1


class TestMatching:
    """Tests for matching functionality."""
    
    def test_match_exact(self, matcher):
        ingredient_id, confidence = matcher.match_single('Tomato')
        assert ingredient_id == 1
        assert confidence > 0.9
    
    def test_match_with_noise(self, matcher):
        ingredient_id, confidence = matcher.match_single('TOMATOES 1kg pack')
        assert ingredient_id == 1
        assert confidence > 0.5
    
    def test_match_misspelled(self, matcher):
        ingredient_id, confidence = matcher.match_single('gralic')
        assert ingredient_id == 3
        assert confidence > 0.5
    
    def test_match_not_found(self, matcher):
        ingredient_id, confidence = matcher.match_single('xyz_unknown_ingredient')
        assert ingredient_id == -1
        assert confidence == 0.0
    
    def test_match_empty_query(self, matcher):
        ingredient_id, confidence = matcher.match_single('')
        assert ingredient_id == -1
        assert confidence == 0.0
    
    def test_match_batch(self, matcher):
        queries = ['Tomato', 'Onion', 'Garlic']
        results = matcher.match_batch(queries)
        assert len(results) == 3
        assert results[0][0] == 1
        assert results[1][0] == 2
        assert results[2][0] == 3


class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_case_insensitive(self, matcher):
        r1 = matcher.match_single('tomato')
        r2 = matcher.match_single('TOMATO')
        r3 = matcher.match_single('ToMaTo')
        assert r1[0] == r2[0] == r3[0] == 1
    
    def test_whitespace_handling(self, matcher):
        r1 = matcher.match_single('tomato')
        r2 = matcher.match_single('  tomato  ')
        r3 = matcher.match_single('tomato   ')
        assert r1[0] == r2[0] == r3[0] == 1
    
    def test_special_characters(self, matcher):
        r1 = matcher.match_single('tomato')
        r2 = matcher.match_single('tomato-red')
        assert r1[0] == r2[0]
