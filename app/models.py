"""
Pydantic models for the FastAPI request/response surface.

Kept deliberately thin — the normalizer returns plain dicts, and these
schemas exist to make the OpenAPI docs useful and to validate input.
"""

from typing import List, Dict
from pydantic import BaseModel, Field, conlist


class NormalizeRequest(BaseModel):
    text: str = Field(
        ...,
        description="Roman Urdu text to normalize. Single word or full sentence.",
        min_length=1,
        max_length=5000,
        json_schema_extra={"example": "yr bht thora kch kya kr rhe ho"},
    )


class TokenRecord(BaseModel):
    original: str
    normalized: str
    source: str = Field(
        ...,
        description='Which resolver matched: "variant_map" | "phonetic" | "unchanged" | "unknown"',
    )
    ambiguous: bool = False
    candidates: List[str] = Field(default_factory=list)


class Stats(BaseModel):
    total: int
    variant_map: int
    phonetic: int
    unchanged: int
    unknown: int
    ambiguous: int


class NormalizeResponse(BaseModel):
    input: str
    normalized: str
    tokens: List[TokenRecord]
    stats: Stats


class BatchNormalizeRequest(BaseModel):
    texts: List[str] = Field(
        ...,
        description="A list of Roman Urdu strings to normalize. Maximum 100 items.",
        min_length=1,
        max_length=100,
    )


class BatchNormalizeResponse(BaseModel):
    results: List[NormalizeResponse]
    count: int


class HealthResponse(BaseModel):
    status: str
    lexicon_size: int
    variant_map_size: int


class LexiconStatsResponse(BaseModel):
    variant_map_entries: int
    canonical_total: int
    total_recognized_spellings: int
    homograph_groups: int
    by_category: Dict[str, int]


class ErrorResponse(BaseModel):
    error: str
    detail: str
