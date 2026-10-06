from pydantic import BaseModel, Field


class MatchRequest(BaseModel):
    resume: dict
    job: dict


class MatchResponse(BaseModel):
    success: bool
    message: str
    data: dict
