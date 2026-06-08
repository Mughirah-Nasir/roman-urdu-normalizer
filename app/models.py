"""
Pydantic models for the FastAPI request/response surface.

Kept deliberately thin — the normalizer returns plain dicts, and these
schemas exist to make the OpenAPI docs useful and to validate input.
"""


from pydantic import BaseModel, Field


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
        description=('Which resolver matched: "variant_map" | "phrase_map" | '
                     '"phonetic" | "unchanged" | "unknown"'),
    )
    confidence: float = Field(
        ...,
        ge=0.0, le=1.0,
        description=("0.0–1.0 confidence the resolution is correct. "
                     "1.0 for explicit map matches, 0.85 for clean phonetic "
                     "matches, 0.40 for ambiguous homographs, 0.0 for unknown."),
    )
    ambiguous: bool = False
    candidates: list[str] = Field(default_factory=list)
    span_tokens: int = Field(
        default=1,
        ge=1,
        description="Number of input tokens consumed by this record. >1 for phrase_map matches.",
    )


class Stats(BaseModel):
    total: int
    variant_map: int
    phrase_map: int = 0
    phonetic: int
    unchanged: int
    unknown: int
    ambiguous: int
    avg_confidence: float | None = Field(
        default=None, description="Mean confidence across all word tokens, or null if no tokens."
    )
    min_confidence: float | None = Field(
        default=None, description="Minimum confidence across all word tokens, or null if no tokens."
    )


class NormalizeResponse(BaseModel):
    input: str
    normalized: str
    tokens: list[TokenRecord]
    stats: Stats


class BatchNormalizeRequest(BaseModel):
    texts: list[str] = Field(
        ...,
        description="A list of Roman Urdu strings to normalize. Maximum 100 items.",
        min_length=1,
        max_length=100,
    )


class BatchNormalizeResponse(BaseModel):
    results: list[NormalizeResponse]
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
    by_category: dict[str, int]


class ErrorResponse(BaseModel):
    error: str
    detail: str
