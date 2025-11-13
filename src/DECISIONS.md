# Fuzzy Entity Matching Pipeline: Design Decisions

## Overview
This document describes the design decisions, architectural choices, and trade-offs made for the fuzzy/entity matching pipeline that maps noisy supplier items to canonical ingredients.

---

## 1. Matching Strategy

### Approach: Hybrid Multi-Stage Matching
The pipeline uses a **cascading matching strategy** with multiple techniques:

1. **Exact Match (Normalized)**: Fast, deterministic path for clean data
2. **Blocking with Token-Set Similarity**: Reduces candidate space to speed up matching
3. **Fuzzy Matching (Levenshtein + Jaro-Winkler)**: Handles misspellings and typos
4. **Semantic Similarity (TF-IDF)**: Captures meaning with common stop-words removed

### Why This Approach?
- **Speed**: Blocking prevents brute-force comparisons across all 10 ingredients for each supplier item
- **Accuracy**: Multi-technique ensemble catches edge cases (typos, synonyms, abbreviations)
- **Robustness**: Handles both exact matches and phonetic/spelling variations
- **Explainability**: Each technique contributes a confidence score; final score is interpretable

### Trade-offs
| Aspect | Choice | Why | Alternative Considered |
|--------|--------|-----|------------------------|
| Speed vs. Accuracy | Multi-stage with blocking | Fast enough for production, high accuracy | Single technique (too slow or inaccurate) |
| Embeddings | TF-IDF instead of BERT | Lightweight, no GPU, interpretable | BERT embeddings (slower, larger footprint) |
| Threshold | 0.6 (65% confidence) | Conservative; flag low-confidence matches | 0.5 (too permissive) or 0.8 (too strict) |
| Tied Scores | Return first match (sorted by ingredient_id) | Deterministic behavior | Random selection (non-reproducible) |

---

## 2. Text Normalization

### Normalization Steps
1. **Lowercase**: `TOMATOES` → `tomatoes`
2. **Remove extra whitespace**: `tomato    paste` → `tomato paste`
3. **Remove pack/size info**: `tomato 1kg` → `tomato`
4. **Handle common abbreviations**: `unslt` → `unsalted`, `jeera` → `cumin`
5. **Stop-words removal**: `red onion` → `onion` (in TF-IDF stage)

### Why?
- **Consistency**: Ensures supplier variants (e.g., `Onion`, `onion`, `ONION`) map to the same canonical form
- **Focus**: Removes noise (sizes, pack info) that doesn't aid matching
- **Coverage**: Handles common misspellings and abbreviations

### Size/Pack Info Removal
Regular expressions strip patterns like `\d+\s*(kg|g|ml|l|pack|box)` (case-insensitive).

---

## 3. Blocking Strategy

### Token-Set Blocking
- **What**: Extract unique tokens from normalized supplier item; only match canonical ingredients that share ≥2 tokens
- **Why**: Dramatically reduces candidate space (10 → 2–3 on average) without losing true matches
- **Trade-off**: Requires canonical list to be pre-tokenized; adds minor overhead

### Example
- Supplier item: `onion red 500g` → normalized: `onion red` → tokens: `{onion, red}`
- Canonical: `Onion` → tokens: `{onion}`
- **Shared**: `{onion}` → **1 token match → blocked out** (only matches if ≥2 shared)
  - ⚠️ Edge case: Single-token ingredients (`Onion`, `Garlic`) pass if ≥1 token match
  - **Decision**: Allow ≥1 token for single-token ingredients to avoid false negatives

---

## 4. Similarity Scoring

### Hybrid Score Calculation
```
Final Score = max(levenshtein_sim, jaro_winkler_sim, tfidf_sim)
```

### Why `max()` Instead of Averaging?
- **Robustness**: If *any* technique strongly suggests a match, we favor it
- **Flexibility**: Catches edge cases where one technique excels (e.g., TF-IDF for semantic matches)
- **Simplicity**: Avoid weighted tuning

### Confidence Threshold
- **0.6**: Matches must be at least 60% similar
- **Conservative**: Prevents false positives; manual review for low-confidence matches
- **Rationale**: In food/ingredient matching, precision > recall (wrong ingredient has high cost)

---

## 5. Failure Modes & Mitigation

### Known Limitations

| Failure Mode | Cause | Mitigation |
|--------------|-------|-----------|
| Abbreviation mismatch (`unslt` ↛ `unsalted`) | Dictionary incomplete | Expand abbreviation dictionary; flag in evaluation |
| Homonyms (`rice` as grain vs. dish) | Single master list | Add context (supplier category, usage); NA for this dataset |
| Partial matches (`tomato juice` ↔ `tomato`) | Tokenization too aggressive | Stop-words list; require word boundaries |
| No match found (<0.6 confidence) | Novel/unknown ingredient | Return `ingredient_id=null, confidence=0.0`; log for manual review |
| Tied scores (same confidence) | Multiple close candidates | Sort by `ingredient_id`, return first; document in output |

### Edge Cases Handled
1. **Empty/Null suppliers**: Skip or return `null` match
2. **Single-token ingredients**: Apply relaxed blocking (≥1 token vs. ≥2)
3. **Case sensitivity**: All normalized to lowercase
4. **Special characters**: Removed during normalization
5. **Duplicate suppliers**: Each row processed independently; no deduplication

---

## 6. Evaluation Metrics

### Metrics Reported
1. **Precision@1**: Of matches with confidence ≥0.6, how many are correct?
2. **Coverage**: % of supplier items with high-confidence match (≥0.6)
3. **Confidence Distribution**: Histogram of match scores for insight into model calibration

### Why These?
- **Precision@1**: Production-critical; wrong match is costly
- **Coverage**: Identifies % of items requiring manual review (confidence <0.6)
- **No Recall**: Ground truth labels not available; Precision@1 serves as proxy for quality

### Benchmarks
- **Target Precision@1**: ≥95% (high confidence in matches)
- **Target Coverage**: ≥80% (most items auto-matched; ~20% flagged for review)

---

## 7. Deployment & API Design

### FastAPI `/match` Endpoint
- **Input**: `{"raw_name": "tomato 1kg"}`
- **Output**: `{"ingredient_id": 1, "confidence": 0.95}`
- **Error Handling**: Invalid input → 400 Bad Request; server error → 500 Internal Server Error

### Why FastAPI?
- Lightweight, async-ready
- Auto-generated OpenAPI docs for testing
- Easy to containerize with Docker

### Scoring Pipeline Flow
```
raw_name 
  → normalize 
  → extract tokens 
  → blocking (candidates) 
  → compute scores 
  → select best 
  → return (ingredient_id, confidence)
```

---

## 8. Production Readiness

### Code Quality
- **Modular Design**: Separate functions for normalization, blocking, scoring, evaluation
- **Type Hints**: Full annotations for clarity and type checking
- **Error Handling**: Try-catch blocks, graceful degradation for edge cases
- **Logging**: Info/warn/error logs for debugging

### Testing
- **Unit Tests** (`pytest`): 
  - Normalization (stopwords, abbreviations, sizes)
  - Blocking logic (token extraction, filtering)
  - Scoring (tied scores, edge cases)
  - API integration (mock requests)
  
### Reproducibility
- `requirements.txt`: Pinned versions
- `setup.sh`: Automated environment setup
- `Dockerfile`: Immutable container image
- Configuration via constants at module top

### Scalability
- Blocking reduces O(n*m) to O(n*k) where k << m
- TF-IDF vectorization is sparse; fits in memory for typical ingredient lists
- No external APIs; fully self-contained

---

## 9. Configuration & Thresholds

### Key Tunable Parameters
```python
MIN_CONFIDENCE = 0.6           # Match threshold
MIN_SHARED_TOKENS = 2          # Blocking threshold (relaxed to 1 for single-token ingredients)
ABBREVIATIONS = {              # Common misspellings/abbreviations
    'unslt': 'unsalted',
    'gralic': 'garlic',
    'jeera': 'cumin',
    ...
}
```

### How to Adjust
- **Lower MIN_CONFIDENCE** (e.g., 0.5): Increase coverage at cost of precision
- **Increase MIN_SHARED_TOKENS** (e.g., 3): Stricter blocking; faster but may miss matches
- **Expand ABBREVIATIONS**: Add supplier-specific abbreviations as discovered

---

## 10. Future Improvements

1. **Learning-based Ranking**: Train a small classifier (logistic regression) on historical matches
2. **Domain Embeddings**: Fine-tune a transformer on food/ingredient corpus for semantic matching
3. **Multi-lingual Support**: Handle supplier items in multiple languages (transliteration)
4. **Feedback Loop**: Log low-confidence matches; periodically retrain/recalibrate thresholds
5. **Batch API**: Support bulk `/match_batch` endpoint for high-volume matching
6. **Caching**: Cache normalized forms and blocking candidates for repeated calls

---

## 11. Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-14 | 1.0 | Initial design; hybrid multi-stage matching with blocking |

