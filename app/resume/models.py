from pydantic import BaseModel, Field


class ResumeExperience(BaseModel):
    position: str | None = None
    company: str | None = None
    startDate: str | None = None
    endDate: str | None = None
    location: str | None = None
    description: list[str] = Field(default_factory=list)


class ResumeEducation(BaseModel):
    degree: str | None = None
    institution: str | None = None
    startDate: str | None = None
    endDate: str | None = None


class ResumeProject(BaseModel):
    name: str | None = None
    startDate: str | None = None
    endDate: str | None = None
    description: list[str] = Field(default_factory=list)


class StructuredResume(BaseModel):
    summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience: list[ResumeExperience] = Field(default_factory=list)
    education: list[ResumeEducation] = Field(default_factory=list)
    projects: list[ResumeProject] = Field(default_factory=list)
