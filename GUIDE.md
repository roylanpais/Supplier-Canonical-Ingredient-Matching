# Ingredient Matcher - Complete Implementation Guide

## Overview

This is a **production-ready fuzzy entity matching system** that maps noisy supplier items to canonical ingredients. It includes:

✅ Text preprocessing (normalization, tokenization, misspelling correction)  
✅ Efficient fuzzy matching (token-set Jaccard + sequence matching)  
✅ Blocking strategy (prefix + token-based candidate filtering)  
✅ FastAPI REST service with /match endpoint  
✅ Batch matching and evaluation scripts  
✅ Unit tests with comprehensive coverage  
✅ Docker containerization  
✅ Production-grade documentation  

---

## File Structure and Organization

### Core Application (`app/`)

```
app/
├── __init__.py                    # Package initialization (empty)
├── preprocessing.py               # Text normalization & tokenization
├── matcher.py                     # Fuzzy matching engine & blocking
└── api.py                         # FastAPI service definition
```

**preprocessing.py**:
- `TextPreprocessor.normalize_text()`: Lowercase, remove units/accents/special chars
- `TextPreprocessor.tokenize()`: Split text, remove stop words
- `TextPreprocessor.correct_misspellings()`: Apply known corrections
- `TextPreprocessor.preprocess()`: Full pipeline

**matcher.py**:
- `BlockingIndex`: Multi-strategy candidate filtering
- `FuzzyMatcher`: Core matching logic with similarity metrics
- `FuzzyMatcher.match_single()`: Match one query
- `FuzzyMatcher.match_batch()`: Match multiple queries

**api.py**:
- `POST /match`: Main endpoint
- `GET /health`: Health check
- `GET /info`: Service info
- Pydantic models for validation

### Tests (`tests/`)

```
tests/
├── __init__.py                    # Package initialization
├── test_matcher.py               # Matcher & preprocessing tests
└── test_api.py                   # API endpoint tests (optional)
```

**test_matcher.py** covers:
- Preprocessing edge cases
- Similarity metrics
- Matching logic
- Batch operations

### Scripts (`scripts/`)

```
scripts/
├── match_items.py                # Batch matching
├── evaluate.py                   # Metrics calculation
└── setup_env.sh                  # Environment setup
```

### Data (`data/`)

```
data/
├── ingredients_master.csv        # INPUT: Canonical ingredients
├── supplier_items.csv            # INPUT: Noisy supplier items
└── matches.csv                   # OUTPUT: Matched results
```

---

## Installation & Setup

### Step 1: Create Project Structure

```bash
mkdir ingredient-matcher
cd ingredient-matcher

# Create directories
mkdir -p app tests scripts data

# Create empty __init__.py files
touch app/__init__.py
touch tests/__init__.py
```

### Step 2: Copy Files

Place the provided files in their respective directories:

```
ingredient-matcher/
├── app/
│   ├── __init__.py
│   ├── preprocessing.py
│   ├── matcher.py
│   └── api.py
├── tests/
│   ├── __init__.py
│   ├── test_matcher.py
│   └── test_api.py
├── scripts/
│   ├── match_items.py
│   ├── evaluate.py
│   └── setup_env.sh
├── data/
│   ├── ingredients_master.csv
│   └── supplier_items.csv
├── Dockerfile
├── requirements.txt
├── DECISIONS.md
├── README.md
└── .dockerignore
```

### Step 3: Install Dependencies

**Linux/macOS:**
```bash
bash scripts/setup_env.sh
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Step 4: Verify Installation

```bash
# Run tests
pytest tests/ -v

# Run batch matching
python scripts/match_items.py

# Run evaluation
python scripts/evaluate.py
```

---

## Usage Patterns

### Pattern 1: Batch Processing

Process all supplier items and save results:

```python
from app.matcher import FuzzyMatcher
import csv

# Load ingredients
ingredients = []
with open('data/ingredients_master.csv', 'r') as f:
    for row in csv.DictReader(f):
        ingredients.append({'ingredient_id': int(row['ingredient_id']), 'name': row['name']})

# Initialize matcher
matcher = FuzzyMatcher(ingredients)

# Process items
items = []
with open('data/supplier_items.csv', 'r') as f:
    for row in csv.DictReader(f):
        items.append(row)

# Match
for item in items:
    ingredient_id, confidence = matcher.match_single(item['raw_name'])
    print(f"{item['item_id']}: {ingredient_id} ({confidence:.2f})")
```

### Pattern 2: Single Query

Match a single item at runtime:

```python
from app.matcher import FuzzyMatcher

# Initialize (load ingredients once)
matcher = FuzzyMatcher(ingredients)

# Match individual query
ingredient_id, confidence = matcher.match_single("TOMATOES 1kg pack")
print(f"Ingredient: {ingredient_id}, Confidence: {confidence}")
```

### Pattern 3: API Usage

Run the FastAPI service:

```bash
uvicorn app.api:app --port 8000
```

Then call the endpoint:

```bash
curl -X POST http://localhost:8000/match \
  -H "Content-Type: application/json" \
  -d '{"raw_name": "TOMATOES 1kg pack"}'
```

---

## Configuration and Tuning

### Adjust Similarity Weights

In `matcher.py`, modify `combined_similarity()`:

```python
# Current: 60% token, 40% string
combined = (0.6 * token_sim) + (0.4 * string_sim)

# Increase token weight for more semantic matching
combined = (0.7 * token_sim) + (0.3 * string_sim)

# Increase string weight for more typo tolerance
combined = (0.5 * token_sim) + (0.5 * string_sim)
```

### Add Stop Words

In `preprocessing.py`, update `STOP_WORDS`:

```python
STOP_WORDS = {
    'pack', 'g', 'kg', 'ml', 'l', 'liter', 'gram',
    # Add more:
    'premium', 'organic', 'fresh', 'frozen'
}
```

### Expand Misspelling Corrections

In `preprocessing.py`, update `CORRECTIONS`:

```python
CORRECTIONS = {
    'gralic': 'garlic',
    'jeera': 'cumin',
    # Add more:
    'tomatoe': 'tomato',
    'onion': 'onion'  # common variations
}
```

### Set Confidence Threshold

In `evaluate.py`, modify threshold:

```python
metrics = evaluate_matches(matches, confidence_threshold=0.7)  # 70% threshold
```

---

## Performance Optimization

### For 100-1K Ingredients (Current)

Use in-memory blocking (current implementation) - no changes needed.

### For 1K-100K Ingredients

Consider pre-computing blocking index:

```python
# Cache blocking index
import pickle

matcher = FuzzyMatcher(ingredients)
with open('blocking_index.pkl', 'wb') as f:
    pickle.dump(matcher.blocking, f)
```

### For >100K Ingredients

Switch to Elasticsearch:

1. Install Elasticsearch
2. Create indices for prefix + token search
3. Update `BlockingIndex.get_candidates()` to query Elasticsearch

---

## Testing and Validation

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test

```bash
pytest tests/test_matcher.py::TestMatching::test_match_exact -v
```

### Check Coverage

```bash
pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html
```

### Add Custom Tests

Create test in `tests/test_matcher.py`:

```python
def test_custom_case(matcher):
    ingredient_id, confidence = matcher.match_single("custom_input")
    assert ingredient_id > 0
    assert confidence > 0.5
```

---

## Docker Deployment

### Build Image

```bash
docker build -t ingredient-matcher:v1.0 .
```

### Run Locally

```bash
docker run -p 8000:8000 ingredient-matcher:v1.0
```

### Push to Registry

```bash
# Tag
docker tag ingredient-matcher:v1.0 myregistry.azurecr.io/ingredient-matcher:v1.0

# Login
az acr login --name myregistry

# Push
docker push myregistry.azurecr.io/ingredient-matcher:v1.0
```

### Deploy to Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ingredient-matcher
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ingredient-matcher
  template:
    metadata:
      labels:
        app: ingredient-matcher
    spec:
      containers:
      - name: matcher
        image: myregistry.azurecr.io/ingredient-matcher:v1.0
        ports:
        - containerPort: 8000
        env:
        - name: INGREDIENTS_FILE
          value: /data/ingredients_master.csv
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
```

---

## Integration with External Systems

### Pattern 1: Python Direct Import

```python
from app.matcher import FuzzyMatcher

# In your application
ingredients = load_from_db()  # Your data source
matcher = FuzzyMatcher(ingredients)
result = matcher.match_single("input_item")
```

### Pattern 2: HTTP API

```python
import requests

response = requests.post(
    'http://localhost:8000/match',
    json={'raw_name': 'TOMATOES 1kg pack'}
)
result = response.json()
print(result['ingredient_id'], result['confidence'])
```

### Pattern 3: Event-Driven (e.g., Kafka)

```python
from app.matcher import FuzzyMatcher

# Consumer
def process_message(msg):
    ingredient_id, confidence = matcher.match_single(msg['raw_name'])
    # Publish result
    producer.send('matches', {'item_id': msg['id'], 'ingredient_id': ingredient_id})
```

---

## Monitoring and Maintenance

### Health Checks

```bash
# Manual check
curl http://localhost:8000/health

# In monitoring tool
curl -f http://localhost:8000/health || exit 1
```

### Metrics to Track

- **Coverage**: % of items matched
- **Precision@1**: % of matches with confidence ≥ 0.5
- **API Latency**: Response time per request
- **Error Rate**: % of failed requests

### Logs

```bash
# Docker
docker logs <container_id>

# Local API
# Check stdout/stderr

# Python logging (optional extension)
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

### Backup & Recovery

```bash
# Backup matches
cp data/matches.csv backups/matches_$(date +%Y%m%d).csv

# Backup ingredients (canonical list)
cp data/ingredients_master.csv backups/
```

---

## Troubleshooting Guide

| Problem | Cause | Solution |
|---------|-------|----------|
| ModuleNotFoundError | Virtual env not activated | `source venv/bin/activate` |
| FileNotFoundError | Missing CSV files | Place in `data/` directory |
| Port in use | Port 8000 occupied | Use `--port 8001` |
| Docker build fails | Docker not running | `docker ps` to verify |
| Low confidence scores | Noisy data format | Expand `STOP_WORDS` or `CORRECTIONS` |
| Timeout on large lists | Too many candidates | Blocking not working; check preprocessing |

---

## Next Steps

1. **Review DECISIONS.md** for architecture rationale
2. **Adjust data files** in `data/` directory
3. **Run batch matching**: `python scripts/match_items.py`
4. **View metrics**: `python scripts/evaluate.py`
5. **Deploy**: Via Docker or local API
6. **Monitor**: Track coverage and precision
7. **Iterate**: Tune stop words and corrections based on results

---

## Support Resources

- **DECISIONS.md**: Design choices and trade-offs
- **README.md**: API documentation
- **SETUP.md**: Installation troubleshooting
- **Tests**: Usage examples in `tests/test_matcher.py`
- **Code comments**: Docstrings in all modules
