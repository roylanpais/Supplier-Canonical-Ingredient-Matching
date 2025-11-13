"""
Ingredient Matcher: Fuzzy Entity Matching Service

A production-ready fuzzy entity matching system that maps noisy supplier items
to canonical ingredients using multi-strategy similarity matching and efficient blocking.

Main Components:
    - TextPreprocessor: Text normalization and tokenization
    - FuzzyMatcher: Multi-metric similarity matching with blocking
    - FastAPI: REST API service with /match endpoint

Example Usage:
    from app.matcher import FuzzyMatcher
    
    ingredients = [
        {'ingredient_id': 1, 'name': 'Tomato'},
        {'ingredient_id': 2, 'name': 'Onion'}
    ]
    
    matcher = FuzzyMatcher(ingredients)
    ingredient_id, confidence = matcher.match_single("TOMATOES 1kg")
    # Output: (1, 0.92)

Modules:
    - preprocessing: Text normalization, tokenization, misspelling correction
    - matcher: Fuzzy matching engine with blocking strategies
    - api: FastAPI service definition

Author: Data Science Team
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Data Science Team"
__title__ = "Ingredient Matcher"
__description__ = "Fuzzy entity matching for supplier items to canonical ingredients"
