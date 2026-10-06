from pydantic import BaseModel, Field


class NormalizedExperience(BaseModel):
    position: str | None = None
    company: str | None = None
    startDate: str | None = None
    endDate: str | None = None
    location: str | None = None
    description: list[str] = Field(default_factory=list)


class NormalizedEducation(BaseModel):
    degree: str | None = None
    institution: str | None = None
    startDate: str | None = None
    endDate: str | None = None


class NormalizedProject(BaseModel):
    name: str | None = None
    startDate: str | None = None
    endDate: str | None = None
    description: list[str] = Field(default_factory=list)


class NormalizedResume(BaseModel):
    summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience: list[NormalizedExperience] = Field(default_factory=list)
    education: list[NormalizedEducation] = Field(default_factory=list)
    projects: list[NormalizedProject] = Field(default_factory=list)
