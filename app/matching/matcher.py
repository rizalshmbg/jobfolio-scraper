from collections.abc import Callable

from ..job.models import StructuredJob
from ..resume.normalized_models import NormalizedResume

from .final_matcher import FinalMatchResult, calculate_final_match
from .models import ExperienceMatchResult
from .qualification_matcher import calculate_qualification_match
from .semantic_matcher import (
    calculate_experience_match,
    calculate_project_match,
)
from .skill_matcher import calculate_skill_match

ExperienceMatcher = Callable[
    [list[dict], list[str]],
    ExperienceMatchResult,
]

ProjectMatcher = Callable[
    [list[dict], list[str]],
    ExperienceMatchResult,
]

QualificationMatcher = Callable[
    [list[dict], list[dict], list[dict], list[str]],
    ExperienceMatchResult,
]


def match_resume_to_job(
    resume: NormalizedResume,
    job: StructuredJob,
    experience_matcher: ExperienceMatcher = calculate_experience_match,
    project_matcher: ProjectMatcher = calculate_project_match,
    qualification_matcher: QualificationMatcher = calculate_qualification_match,
) -> FinalMatchResult:

    # --------------------------------------------------
    # Required Skill Match
    # --------------------------------------------------

    required_skill_result = calculate_skill_match(
        resume_skills=resume.skills,
        required_skills=job.requiredSkills,
    )

    # --------------------------------------------------
    # Experience Match
    # --------------------------------------------------

    experience_result = experience_matcher(
        experience=[experience.model_dump() for experience in resume.experience],
        responsibilities=job.responsibilities,
    )

    # --------------------------------------------------
    # Project Match
    # --------------------------------------------------

    project_result = project_matcher(
        projects=[project.model_dump() for project in resume.projects],
        responsibilities=job.responsibilities,
    )

    # --------------------------------------------------
    # Qualification Match
    # --------------------------------------------------

    qualification_result = qualification_matcher(
        education=[education.model_dump() for education in resume.education],
        experience=[experience.model_dump() for experience in resume.experience],
        projects=[project.model_dump() for project in resume.projects],
        qualifications=job.qualifications,
    )

    # --------------------------------------------------
    # Final Match
    # --------------------------------------------------

    return calculate_final_match(
        required_skill_result=required_skill_result,
        experience_result=experience_result,
        project_result=project_result,
        qualification_result=qualification_result,
        resume_skills=resume.skills,
        preferred_skills=job.preferredSkills,
    )
