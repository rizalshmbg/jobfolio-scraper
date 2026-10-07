from pydantic import BaseModel, Field


class MatchRequest(BaseModel):
    resume: dict
    job: dict


class MatchResponse(BaseModel):
    success: bool
    message: str
    data: dict


class AnalyzeAndMatchJob(BaseModel):
    company: str | None = None
    position: str | None = None
    description: str | None = None
    requirements: list[str] = Field(default_factory=list)
    location: str | None = None
    employmentType: str | None = None
    workArrangement: str | None = None


class AnalyzeAndMatchResponse(BaseModel):
    success: bool
    message: str
    data: dict
