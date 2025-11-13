import pandas as pd
from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
import nltk

from .models import MatchRequest, MatchResponse
from .matching import Matcher
from .config import MASTER_FILE, MATCH_THRESHOLD

# Global matcher instance
matcher_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Asynchronous context manager for app lifespan events.
    Handles startup (model loading) and shutdown.
    """
    # --- Startup ---
    print("Application startup: Loading NLTK data and matcher...")
    global matcher_instance
    
    # Ensure NLTK data is downloaded
    try:
        nltk.data.find('corpora/stopwords')
        nltk.data.find('corpora/wordnet')
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        print("Downloading NLTK data...")
        nltk.download('stopwords')
        nltk.download('wordnet')
        nltk.download('punkt')
    
    # Load master data and initialize the matcher
    try:
        master_data = pd.read_csv(MASTER_FILE)
        # Ensure ID is string for consistency
        master_data['ingredient_id'] = master_data['ingredient_id'].astype(str)
        matcher_instance = Matcher(master_data)
        print("Matcher loaded successfully.")
    except FileNotFoundError:
        print(f"FATAL ERROR: Master file not found at {MASTER_FILE}")
        # In a real app, you might exit or handle this more gracefully
        matcher_instance = None
    except Exception as e:
        print(f"FATAL ERROR: Failed to load matcher: {e}")
        matcher_instance = None
    
    yield  # API is now running
    
    # --- Shutdown ---
    print("Application shutdown.")
    matcher_instance = None


app = FastAPI(
    title="Ingredient Matching API",
    description="Fuzzy matches supplier items to a canonical ingredient list.",
    version="1.0.0",
    lifespan=lifespan
)

def get_matcher() -> Matcher:
    """
    Dependency injection function to get the global matcher instance.
    Raises a 503 error if the matcher failed to load.
    """
    if matcher_instance is None:
        raise HTTPException(
            status_code=503, 
            detail="Matcher is not available or failed to load. Please check server logs."
        )
    return matcher_instance

@app.get("/", summary="Health Check")
def read_root():
    """Root endpoint for simple health checks."""
    return {"status": "ok", "message": "Ingredient Matching API is running."}


@app.post("/match", 
          response_model=MatchResponse,
          summary="Match a single supplier item",
          description="Receives a raw item name and returns the single best-matching canonical ingredient ID and a confidence score.")
def match_item(
    request: MatchRequest, 
    matcher: Matcher = Depends(get_matcher)
) -> MatchResponse:
    """
    Matches a single raw item name against the canonical list.
    """
    try:
        ingredient_id, confidence = matcher.match(
            request.raw_name, 
            threshold=MATCH_THRESHOLD
        )
        
        return MatchResponse(
            ingredient_id=ingredient_id, 
            confidence=confidence
        )
    except Exception as e:
        # Generic error handler for unexpected issues during matching
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during matching: {e}"
        )