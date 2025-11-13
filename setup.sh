#!/bin/bash

set -e

echo "Setting up Ingredient Matcher environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip setuptools wheel
pip install -q -r requirements.txt

# Create data directory if it doesn't exist
mkdir -p data

# Verify data files
if [ ! -f "data/ingredients_master.csv" ]; then
    echo "⚠ Warning: data/ingredients_master.csv not found"
fi

if [ ! -f "data/supplier_items.csv" ]; then
    echo "⚠ Warning: data/supplier_items.csv not found"
fi

echo ""
echo "✓ Environment setup complete!"
echo ""
echo "Usage:"
echo "  source venv/bin/activate              # Activate virtual environment"
echo "  python scripts/match_items.py         # Run batch matching"
echo "  python scripts/evaluate.py            # Run evaluation"
echo "  pytest tests/                         # Run unit tests"
echo "  uvicorn app.api:app --reload         # Run API locally (http://localhost:8000)"
echo ""
echo "Testing:"
echo "  pytest tests/ -v                      # Run all tests with verbose output"
echo ""
