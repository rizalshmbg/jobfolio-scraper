from pydantic import BaseModel, Field


class SemanticMatch(BaseModel):
    matched: bool
    relevance: str
    evidence: list[str] = Field(default_factory=list)


class ExperienceMatchResult(BaseModel):
    score: float
    matches: list[SemanticMatch] = Field(default_factory=list)
