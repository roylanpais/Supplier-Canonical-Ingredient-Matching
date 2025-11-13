"""FastAPI service for ingredient matching."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import csv
import os
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from matcher import FuzzyMatcher
from preprocessing import TextPreprocessor

app = FastAPI(
    title="Ingredient Matcher API",
    version="1.0.0",
    description="Fuzzy entity matching for supplier items to canonical ingredients"
)

# Configuration
INGREDIENTS_FILE = os.getenv('INGREDIENTS_FILE', 'data/ingredients_master.csv')


def load_ingredients():
    """Load canonical ingredients from CSV."""
    ingredients = []
    if not os.path.exists(INGREDIENTS_FILE):
        raise FileNotFoundError(f"Ingredients file not found: {INGREDIENTS_FILE}")
    
    with open(INGREDIENTS_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ingredients.append({
                'ingredient_id': int(row['ingredient_id']),
                'name': row['name']
            })
    return ingredients


# Initialize matcher at startup
try:
    ingredients = load_ingredients()
    matcher = FuzzyMatcher(ingredients)
except Exception as e:
    raise RuntimeError(f"Failed to initialize matcher: {e}")


# Request/Response schemas
class MatchRequest(BaseModel):
    """Request schema for match endpoint."""
    raw_name: str
    
    class Config:
        example = {"raw_name": "TOMATOES 1kg pack"}


class MatchResponse(BaseModel):
    """Response schema for match endpoint."""
    ingredient_id: int
    confidence: float
    matched_ingredient: Optional[str] = None
    
    class Config:
        example = {
            "ingredient_id": 1,
            "confidence": 0.92,
            "matched_ingredient": "Tomato"
        }


@app.post("/match", response_model=MatchResponse)
async def match_item(request: MatchRequest):
    """Match a supplier item to a canonical ingredient."""
    if not request.raw_name or not request.raw_name.strip():
        raise HTTPException(status_code=400, detail="raw_name cannot be empty")
    
    # Match the item
    ingredient_id, confidence = matcher.match_single(request.raw_name)
    
    # Get matched ingredient name for reference
    matched_name = None
    if ingredient_id > 0:
        for ing in ingredients:
            if ing['ingredient_id'] == ingredient_id:
                matched_name = ing['name']
                break
    
    return MatchResponse(
        ingredient_id=ingredient_id,
        confidence=float(confidence),
        matched_ingredient=matched_name
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "ingredient-matcher"}


@app.get("/info")
async def service_info():
    """Service information endpoint."""
    return {
        "service": "Ingredient Matcher",
        "version": "1.0.0",
        "ingredients_loaded": len(ingredients),
        "algorithms": ["token-set-jaccard", "sequence-matching", "prefix-blocking"]
    }
