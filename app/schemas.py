from pydantic import BaseModel, Field
from typing import Literal

class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=12000)
    use_ai: bool = True

class Suggestion(BaseModel):
    id: str
    mark: str
    kind: str
    start: int
    end: int
    confidence: float = Field(ge=0, le=1)
    explanation: str
    alternatives: list[str] = []

class AnalyzeResponse(BaseModel):
    text: str
    suggestions: list[Suggestion]
    corrected_text: str
    engine: Literal["python", "ai+python", "ai"]
    notes: list[str] = []
