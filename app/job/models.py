from typing import Literal

from pydantic import BaseModel, Field


class SkillRequirement(BaseModel):
    skills: list[str] = Field(default_factory=list)
    operator: Literal["AND", "OR"] = "AND"


class StructuredJob(BaseModel):
    title: str | None = None
    company: str | None = None
    description: str | None = None
    location: str | None = None
    employmentType: str | None = None
    workArrangement: str | None = None
    requiredSkills: list[SkillRequirement] = Field(default_factory=list)
    preferredSkills: list[SkillRequirement] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    qualifications: list[str] = Field(default_factory=list)
