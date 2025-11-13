#!/bin/bash
# Setup script for reproducible environment

set -e  # Exit on error

echo "=== Fuzzy Ingredient Matcher Setup ==="

# Create Python virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create data directory if not exists
mkdir -p data

# Run tests
echo "Running unit tests..."
pytest test_matcher.py -v

# Run pipeline to generate matches.csv
echo "Running matching pipeline..."
python matcher.py

# Report
echo ""
echo "=== Setup Complete ==="
echo ""
echo "To run the FastAPI server:"
echo "  python app.py"
echo ""
echo "Then test the /match endpoint:"
echo "  curl -X POST http://localhost:8000/match \\
    -H 'Content-Type: application/json' \\
    -d '{\"raw_name\": \"tomato 1kg\"}'"
echo ""
echo "OpenAPI docs: http://localhost:8000/docs"
echo ""
