import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path
import time

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from app.main import app

@pytest.fixture(scope="module")
def client():
    """Create a TestClient instance for the API."""
    # The client will automatically handle the lifespan events (startup/shutdown)
    with TestClient(app) as c:
        # We need to give the startup event time to run and load the model
        # In a real CI/CD, you might use a more robust readiness check
        time.sleep(1) # Give 1s for the model to load
        yield c

def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Ingredient Matching API is running."}

def test_match_api_exact(client):
    response = client.post("/match", json={"raw_name": "TOMATOES 1kg pack"})
    assert response.status_code == 200
    data = response.json()
    assert data['ingredient_id'] == '1'
    assert data['confidence'] == 1.0

def test_match_api_misspelling(client):
    response = client.post("/match", json={"raw_name": "gralic peeled 100g"})
    assert response.status_code == 200
    data = response.json()
    assert data['ingredient_id'] == '3'
    assert data['confidence'] == 1.0

def test_match_api_synonym_jeera(client):
    response = client.post("/match", json={"raw_name": "jeera 50g"})
    assert response.status_code == 200
    data = response.json()
    assert data['ingredient_id'] == '6'
    assert data['confidence'] == 1.0 # 'jeera' -> 'cumin'

def test_match_api_synonym_flour(client):
    response = client.post("/match", json={"raw_name": "plain flour 1kg"})
    assert response.status_code == 200
    data = response.json()
    assert data['ingredient_id'] == '8'
    assert data['confidence'] == 1.0

def test_match_api_synonym_butter(client):
    response = client.post("/match", json={"raw_name": "butter unslt"})
    assert response.status_code == 200
    data = response.json()
    assert data['ingredient_id'] == '9'
    assert data['confidence'] == 1.0

def test_match_api_no_good_match(client):
    response = client.post("/match", json={"raw_name": "Dragon Fruit"})
    assert response.status_code == 200
    data = response.json()
    assert data['ingredient_id'] is not None # Returns best match
    assert data['confidence'] < 0.7 # Best match is low confidence

def test_match_api_empty_query(client):
    response = client.post("/match", json={"raw_name": ""})
    assert response.status_code == 200
    data = response.json()
    assert data['ingredient_id'] is None
    assert data['confidence'] == 0.0

def test_match_api_validation_error(client):
    # Test with a bad request body
    response = client.post("/match", json={"wrong_key": "tomato"})
    assert response.status_code == 422 # Unprocessable Entity