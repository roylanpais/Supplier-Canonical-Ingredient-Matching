# Ingredient Matcher - Setup Instructions

## Prerequisites

- Python 3.10+
- Docker (optional, for containerized deployment)
- `pip` or `conda` package manager

## Installation

### Option 1: Local Setup (Linux/macOS)

```bash
# Navigate to project directory
cd ingredient-matcher

# Run automated setup
bash scripts/setup_env.sh

# Verify installation
source venv/bin/activate
pytest tests/ -v
```

### Option 2: Local Setup (Windows)

```bash
cd ingredient-matcher

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
pytest tests\ -v
```

### Option 3: Docker (All Platforms)

```bash
# Build image
docker build -t ingredient-matcher .

# Run container
docker run -p 8000:8000 ingredient-matcher
```

## Verify Installation

### Test 1: Unit Tests
```bash
source venv/bin/activate  # or activate as above
pytest tests/ -v
```

Expected output:
```
tests/test_matcher.py::TestPreprocessing::test_normalize_text_lowercase PASSED
tests/test_matcher.py::TestPreprocessing::test_tokenize PASSED
...
tests/test_api.py::TestAPIEndpoints::test_match_valid_request PASSED

====== X passed in Y.XXs ======
```

### Test 2: Batch Matching
```bash
python scripts/match_items.py
```

Expected output:
```
Loading data...
Loaded 10 canonical ingredients
Loaded 10 supplier items

Matching items...
  A01: 'TOMATOES 1kg pack' -> ID 1 (0.9200)
  A02: 'onion red 500g' -> ID 2 (0.8700)
  ...

Matches saved to data/matches.csv
```

### Test 3: Evaluation
```bash
python scripts/evaluate.py
```

Expected output:
```
Evaluation Report
============================================================
Total Items:           10
Coverage:              100.00%
Precision@1 (≥0.50):   100.00%
Avg Confidence:        0.8765
Min Confidence:        0.6200
Max Confidence:        0.9900

Confidence Distribution:
  0.6: 1 items
  0.8: 4 items
  0.9: 5 items
```

### Test 4: API Service
```bash
# Terminal 1: Start server
source venv/bin/activate
uvicorn app.api:app --reload --port 8000

# Terminal 2: Test endpoint
curl -X POST http://localhost:8000/match \
  -H "Content-Type: application/json" \
  -d '{"raw_name": "TOMATOES 1kg pack"}'
```

Expected response:
```json
{
  "ingredient_id": 1,
  "confidence": 0.92,
  "matched_ingredient": "Tomato"
}
```

## File Placement

Ensure data files are in correct location:

```
ingredient-matcher/
├── data/
│   ├── ingredients_master.csv   ← Place canonical ingredients here
│   └── supplier_items.csv        ← Place supplier items here
```

If data is in different location, set environment variable:

```bash
export INGREDIENTS_FILE=/path/to/ingredients_master.csv
uvicorn app.api:app
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'fastapi'"

**Solution**: Ensure virtual environment is activated
```bash
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

### Issue: "FileNotFoundError: ingredients_master.csv"

**Solution**: Place CSV files in `data/` directory or set `INGREDIENTS_FILE` env var:
```bash
export INGREDIENTS_FILE=data/ingredients_master.csv
python scripts/match_items.py
```

### Issue: Docker build fails

**Solution**: Ensure Docker is installed and running:
```bash
docker --version
docker run hello-world
```

### Issue: Port 8000 already in use

**Solution**: Use different port:
```bash
uvicorn app.api:app --port 8001
# or kill process on 8000
lsof -i :8000
kill -9 <PID>
```

## Performance Tips

1. **Batch Processing**: Use `matcher.match_batch()` instead of repeated `match_single()` calls
2. **Caching**: Implement Redis caching for repeated queries
3. **Async**: API supports concurrent requests via uvicorn workers

```bash
# Run with multiple workers for higher concurrency
uvicorn app.api:app --workers 4 --port 8000
```

## Next Steps

1. **Review DECISIONS.md** for architectural choices
2. **Explore test cases** in `tests/` for expected behavior
3. **Try different queries** via API to understand confidence scores
4. **Tune thresholds** based on evaluation metrics
5. **Extend stop words** if precision drops on your data

## Support

For issues or questions:
1. Check DECISIONS.md for design rationale
2. Review README.md for API documentation
3. Examine test files for usage examples
4. Check container logs: `docker logs <container_id>`
