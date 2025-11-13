from pydantic import BaseModel

class MatchRequest(BaseModel):
    """Pydantic model for the /match request body."""
    raw_name: str

class MatchResponse(BaseModel):
    """Pydantic model for the /match response body."""
    ingredient_id: str | None
    confidence: float