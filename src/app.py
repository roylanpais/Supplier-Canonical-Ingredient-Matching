"""
FastAPI Service for Fuzzy Entity Matching
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import logging
from pathlib import Path

from matcher import (
    load_master_ingredients,
    preprocess_text,
    MatchingEngine,
    SupplierItem,
    MIN_CONFIDENCE_THRESHOLD,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# API Models
# ============================================================================

class MatchRequest(BaseModel):
    """Request body for /match endpoint."""
    raw_name: str = Field(..., description="Noisy supplier item name")


class MatchResponse(BaseModel):
    """Response body for /match endpoint."""
    ingredient_id: Optional[int] = Field(..., description="Matched ingredient ID or null")
    confidence: float = Field(..., description="Confidence score [0, 1]")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Ingredient Matcher",
    description="Fuzzy entity matching service for supplier items to canonical ingredients",
    version="1.0.0"
)

# Global state: Matching engine initialized at startup
matching_engine: Optional[MatchingEngine] = None


@app.on_event("startup")
async def startup_event():
    """Initialize matching engine at startup."""
    global matching_engine
    try:
        master_file = Path('data/ingredients_master.csv')
        if not master_file.exists():
            raise FileNotFoundError(f"Master file not found: {master_file}")
        
        ingredients = load_master_ingredients(master_file)
        matching_engine = MatchingEngine(ingredients)
        logger.info("Matching engine initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize matching engine: {e}")
        raise


@app.post("/match", response_model=MatchResponse)
async def match_item(request: MatchRequest) -> MatchResponse:
    """
    Match a noisy supplier item name to a canonical ingredient.
    
    Args:
        request: JSON body with "raw_name" field.
    
    Returns:
        JSON with "ingredient_id" and "confidence".
    
    Raises:
        HTTPException: If matching engine not initialized or input invalid.
    """
    if matching_engine is None:
        logger.error("Matching engine not initialized")
        raise HTTPException(status_code=500, detail="Matching engine not initialized")
    
    try:
        # Validate input
        if not request.raw_name or not request.raw_name.strip():
            raise HTTPException(status_code=400, detail="raw_name cannot be empty")
        
        # Preprocess
        normalized_name, tokens = preprocess_text(request.raw_name)
        supplier_item = SupplierItem(
            item_id="api_request",
            raw_name=request.raw_name,
            normalized_name=normalized_name,
            tokens=tokens
        )
        
        # Match
        match_result = matching_engine.match(supplier_item)
        
        return MatchResponse(
            ingredient_id=match_result.ingredient_id,
            confidence=match_result.confidence
        )
    
    except Exception as e:
        logger.error(f"Error matching '{request.raw_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Matching error: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "engine_initialized": matching_engine is not None}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Ingredient Matcher",
        "version": "1.0.0",
        "endpoints": {
            "POST /match": "Match supplier item to ingredient",
            "GET /health": "Health check",
            "GET /docs": "OpenAPI documentation"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
