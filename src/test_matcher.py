"""
Unit Tests for Fuzzy Entity Matching Pipeline
Tests cover normalization, blocking, scoring, and API integration.
"""

import pytest
from pathlib import Path
from typing import List

from matcher import (
    normalize_text,
    remove_size_info,
    expand_abbreviations,
    preprocess_text,
    levenshtein_similarity,
    jaro_winkler_similarity,
    get_blocking_candidates,
    build_tfidf_vectors,
    tfidf_similarity,
    MatchingEngine,
    Ingredient,
    SupplierItem,
    Match,
    load_master_ingredients,
    STOP_WORDS,
)
from app import app
from fastapi.testclient import TestClient


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_ingredients() -> List[Ingredient]:
    """Sample canonical ingredients."""
    return [
        Ingredient(ingredient_id=1, name="Tomato", normalized_name="tomato", tokens={"tomato"}),
        Ingredient(ingredient_id=2, name="Onion", normalized_name="onion", tokens={"onion"}),
        Ingredient(ingredient_id=3, name="Garlic", normalized_name="garlic", tokens={"garlic"}),
        Ingredient(ingredient_id=4, name="Whole Milk", normalized_name="whole milk", tokens={"whole", "milk"}),
        Ingredient(ingredient_id=5, name="Olive Oil", normalized_name="olive oil", tokens={"olive", "oil"}),
    ]


@pytest.fixture
def test_client():
    """FastAPI test client."""
    return TestClient(app)


# ============================================================================
# Normalization Tests
# ============================================================================

class TestNormalization:
    """Test text normalization."""
    
    def test_normalize_lowercase(self):
        """Lowercase conversion."""
        assert normalize_text("TOMATO") == "tomato"
        assert normalize_text("ToMaTo") == "tomato"
    
    def test_normalize_whitespace(self):
        """Extra whitespace removal."""
        assert normalize_text("tomato    paste") == "tomato paste"
        assert normalize_text("  tomato  ") == "tomato"
    
    def test_normalize_special_chars(self):
        """Special character removal."""
        assert normalize_text("tomato!@#$%") == "tomato"
        assert normalize_text("tom-ato") == "tom ato"
    
    def test_normalize_empty(self):
        """Empty string handling."""
        assert normalize_text("") == ""
        assert normalize_text("   ") == ""


class TestSizeRemoval:
    """Test pack/size info removal."""
    
    def test_remove_kg(self):
        """Remove kilogram."""
        assert remove_size_info("tomato 1kg") == "tomato"
        assert remove_size_info("tomato 2.5 kg") == "tomato"
    
    def test_remove_ml(self):
        """Remove milliliter."""
        assert remove_size_info("milk 500ml") == "milk"
        assert remove_size_info("milk 1 l") == "milk"
    
    def test_remove_pack(self):
        """Remove pack/box."""
        assert remove_size_info("tomato 1 pack") == "tomato"
        assert remove_size_info("tomato 2box") == "tomato"
    
    def test_remove_multiple(self):
        """Remove multiple size patterns."""
        assert remove_size_info("tomato 1kg 2pack") == "tomato"


class TestAbbreviations:
    """Test abbreviation expansion."""
    
    def test_expand_unsalted(self):
        """Expand 'unslt' to 'unsalted'."""
        assert "unsalted" in expand_abbreviations("butter unslt").lower()
    
    def test_expand_garlic(self):
        """Expand 'gralic' to 'garlic'."""
        assert "garlic" in expand_abbreviations("gralic").lower()
    
    def test_expand_jeera(self):
        """Expand 'jeera' to 'cumin'."""
        assert "cumin" in expand_abbreviations("jeera").lower()
    
    def test_no_expansion_needed(self):
        """No expansion when not needed."""
        assert expand_abbreviations("tomato") == "tomato"


class TestPreprocessing:
    """Test full preprocessing pipeline."""
    
    def test_preprocess_complex(self):
        """Complex preprocessing example."""
        text, tokens = preprocess_text("TOMATO 1kg PACK")
        assert text == "tomato"
        assert tokens == {"tomato"}
    
    def test_preprocess_with_abbreviation(self):
        """Preprocessing with abbreviation."""
        text, tokens = preprocess_text("butter unslt 250 g")
        assert "unsalted" in text
        assert "butter" in tokens
    
    def test_preprocess_multi_token(self):
        """Multi-token preprocessing."""
        text, tokens = preprocess_text("extra virgin olive oil 500ml")
        assert "olive" in tokens
        assert "oil" in tokens


# ============================================================================
# Similarity Tests
# ============================================================================

class TestSimilarityMetrics:
    """Test similarity calculations."""
    
    def test_levenshtein_exact(self):
        """Exact match."""
        assert levenshtein_similarity("tomato", "tomato") == 1.0
    
    def test_levenshtein_typo(self):
        """Typo handling."""
        sim = levenshtein_similarity("tomato", "toamto")
        assert sim > 0.8
    
    def test_levenshtein_partial(self):
        """Partial match."""
        sim = levenshtein_similarity("tomato", "tom")
        assert sim > 0.4
    
    def test_jaro_winkler_exact(self):
        """Exact match."""
        assert jaro_winkler_similarity("tomato", "tomato") == 1.0
    
    def test_jaro_winkler_prefix(self):
        """Prefix bonus."""
        sim1 = jaro_winkler_similarity("tomato", "tom")
        sim2 = jaro_winkler_similarity("tomato", "mato")
        # Jaro-Winkler gives extra points for prefix matches
        assert sim1 >= sim2
    
    def test_similarity_empty(self):
        """Empty strings."""
        assert levenshtein_similarity("", "") == 1.0
        assert jaro_winkler_similarity("", "") == 1.0


class TestTFIDFSimilarity:
    """Test TF-IDF similarity."""
    
    def test_tfidf_exact(self):
        """Exact semantic match."""
        texts = ["tomato", "tomato"]
        vectors = build_tfidf_vectors(texts, STOP_WORDS)
        sim = tfidf_similarity(vectors["tomato"], vectors["tomato"])
        assert sim == 1.0
    
    def test_tfidf_different(self):
        """Different documents."""
        texts = ["tomato red", "onion white"]
        vectors = build_tfidf_vectors(texts, STOP_WORDS)
        sim = tfidf_similarity(vectors["tomato red"], vectors["onion white"])
        assert sim == 0.0
    
    def test_tfidf_empty(self):
        """Empty vector."""
        sim = tfidf_similarity({}, {"word": 1.0})
        assert sim == 0.0


# ============================================================================
# Blocking Tests
# ============================================================================

class TestBlocking:
    """Test blocking strategy."""
    
    def test_blocking_exact(self, sample_ingredients):
        """Exact token match."""
        supplier = SupplierItem("A01", "tomato", "tomato", {"tomato"})
        candidates = get_blocking_candidates(supplier, sample_ingredients)
        assert any(ing.ingredient_id == 1 for ing in candidates)
    
    def test_blocking_multi_token(self, sample_ingredients):
        """Multi-token matching."""
        supplier = SupplierItem("A05", "olive oil", "olive oil", {"olive", "oil"})
        candidates = get_blocking_candidates(supplier, sample_ingredients)
        assert any(ing.ingredient_id == 5 for ing in candidates)
    
    def test_blocking_single_token_ingredient(self, sample_ingredients):
        """Single-token ingredient relaxed blocking."""
        supplier = SupplierItem("A01", "red tomato", "red tomato", {"red", "tomato"})
        candidates = get_blocking_candidates(supplier, sample_ingredients)
        # Should include Tomato (single-token) with >= 1 shared token
        assert any(ing.ingredient_id == 1 for ing in candidates)
    
    def test_blocking_no_match(self, sample_ingredients):
        """No blocking match."""
        supplier = SupplierItem("A99", "xyz unknown", "xyz unknown", {"xyz", "unknown"})
        candidates = get_blocking_candidates(supplier, sample_ingredients)
        assert len(candidates) == 0


# ============================================================================
# Matching Engine Tests
# ============================================================================

class TestMatchingEngine:
    """Test matching engine."""
    
    def test_engine_initialization(self, sample_ingredients):
        """Engine initialization."""
        engine = MatchingEngine(sample_ingredients)
        assert engine.ingredients == sample_ingredients
        assert len(engine.tfidf_vectors) == len(sample_ingredients)
    
    def test_match_exact(self, sample_ingredients):
        """Exact match."""
        engine = MatchingEngine(sample_ingredients)
        supplier = SupplierItem("A01", "TOMATO 1kg", "tomato", {"tomato"})
        match = engine.match(supplier)
        assert match.ingredient_id == 1
        assert match.confidence >= 0.9
    
    def test_match_typo(self, sample_ingredients):
        """Typo in supplier item."""
        engine = MatchingEngine(sample_ingredients)
        supplier = SupplierItem("A03", "gralic peeled", "garlic peeled", {"garlic", "peeled"})
        match = engine.match(supplier)
        assert match.ingredient_id == 3
    
    def test_match_no_candidate(self, sample_ingredients):
        """No candidate found."""
        engine = MatchingEngine(sample_ingredients)
        supplier = SupplierItem("A99", "xyz unknown", "xyz unknown", {"xyz", "unknown"})
        match = engine.match(supplier)
        assert match.ingredient_id is None
        assert match.confidence == 0.0
    
    def test_match_low_confidence(self, sample_ingredients):
        """Low confidence match (but still returned)."""
        engine = MatchingEngine(sample_ingredients)
        # Completely different word
        supplier = SupplierItem("A98", "elephant", "elephant", {"elephant"})
        match = engine.match(supplier)
        # May have no candidate due to blocking; else low confidence
        assert match.confidence <= 0.6 or match.ingredient_id is None
    
    def test_match_deterministic(self, sample_ingredients):
        """Tied scores resolved deterministically."""
        engine = MatchingEngine(sample_ingredients)
        supplier = SupplierItem("A01", "tomato", "tomato", {"tomato"})
        match1 = engine.match(supplier)
        match2 = engine.match(supplier)
        assert match1.ingredient_id == match2.ingredient_id
        assert match1.confidence == match2.confidence


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases."""
    
    def test_empty_supplier_name(self, sample_ingredients):
        """Empty supplier item name."""
        engine = MatchingEngine(sample_ingredients)
        supplier = SupplierItem("A99", "", "", set())
        match = engine.match(supplier)
        assert match.ingredient_id is None
    
    def test_only_size_info(self, sample_ingredients):
        """Only size info, no ingredient name."""
        engine = MatchingEngine(sample_ingredients)
        supplier = SupplierItem("A99", "1kg pack", "", set())
        match = engine.match(supplier)
        assert match.ingredient_id is None
    
    def test_unicode_handling(self, sample_ingredients):
        """Unicode characters."""
        engine = MatchingEngine(sample_ingredients)
        supplier = SupplierItem("A01", "tömätö", "tomato", {"tomato"})
        # Should normalize without crashing
        match = engine.match(supplier)
        # Match quality depends on normalization
        assert match is not None
    
    def test_very_long_name(self, sample_ingredients):
        """Very long supplier name."""
        long_name = "tomato " + "extra " * 100 + "1kg"
        engine = MatchingEngine(sample_ingredients)
        supplier = SupplierItem("A01", long_name, "tomato extra", {"tomato", "extra"})
        match = engine.match(supplier)
        # Should still work
        assert match is not None


# ============================================================================
# FastAPI Integration Tests
# ============================================================================

class TestFastAPIIntegration:
    """Test FastAPI endpoints."""
    
    def test_health_check(self, test_client):
        """Health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()
    
    def test_root_endpoint(self, test_client):
        """Root endpoint."""
        response = test_client.get("/")
        assert response.status_code == 200
        assert "service" in response.json()
    
    def test_match_endpoint_valid(self, test_client):
        """Match endpoint with valid input."""
        response = test_client.post("/match", json={"raw_name": "tomato 1kg"})
        assert response.status_code == 200
        data = response.json()
        assert "ingredient_id" in data
        assert "confidence" in data
    
    def test_match_endpoint_empty(self, test_client):
        """Match endpoint with empty input."""
        response = test_client.post("/match", json={"raw_name": ""})
        assert response.status_code == 400
    
    def test_match_endpoint_missing_field(self, test_client):
        """Match endpoint with missing field."""
        response = test_client.post("/match", json={})
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_match_endpoint_response_model(self, test_client):
        """Match endpoint response schema."""
        response = test_client.post("/match", json={"raw_name": "onion"})
        assert response.status_code == 200
        data = response.json()
        # ingredient_id should be int or null
        assert data["ingredient_id"] is None or isinstance(data["ingredient_id"], int)
        # confidence should be float in [0, 1]
        assert 0.0 <= data["confidence"] <= 1.0


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
