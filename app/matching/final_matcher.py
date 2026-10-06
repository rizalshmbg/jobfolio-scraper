from dataclasses import dataclass, field

from .models import ExperienceMatchResult, SemanticMatch
from .skill_matcher import SkillMatchResult

EXPERIENCE_WEIGHT = 35.0
REQUIRED_SKILLS_WEIGHT = 25.0
PROJECTS_WEIGHT = 20.0
QUALIFICATIONS_WEIGHT = 10.0
PREFERRED_SKILLS_WEIGHT = 10.0


@dataclass
class FinalMatchResult:
    final_score: float

    required_skills_score: float
    experience_score: float
    projects_score: float
    qualification_score: float

    preferred_skills_score: float | None
    preferred_skills_available: bool

    matched_required_skills: list[str] = field(default_factory=list)
    missing_required_skills: list[str] = field(default_factory=list)

    matched_preferred_skills: list[str] = field(default_factory=list)

    experience_matches: list[SemanticMatch] = field(default_factory=list)
    project_matches: list[SemanticMatch] = field(default_factory=list)
    qualification_matches: list[SemanticMatch] = field(default_factory=list)


def calculate_final_match(
    required_skill_result: SkillMatchResult,
    experience_result: ExperienceMatchResult,
    project_result: ExperienceMatchResult,
    qualification_result: ExperienceMatchResult,
    resume_skills: list[str],
    preferred_skills: list[str],
) -> FinalMatchResult:

    required_skills_score = required_skill_result.score
    experience_score = experience_result.score
    projects_score = project_result.score
    qualification_score = qualification_result.score

    available_components = [
        (REQUIRED_SKILLS_WEIGHT, required_skills_score),
        (EXPERIENCE_WEIGHT, experience_score),
        (PROJECTS_WEIGHT, projects_score),
        (QUALIFICATIONS_WEIGHT, qualification_score),
    ]

    resume_skill_set = set(resume_skills)
    preferred_skill_set = set(preferred_skills)

    if preferred_skill_set:
        matched_preferred_skills = sorted(resume_skill_set & preferred_skill_set)

        preferred_skills_score = (
            len(matched_preferred_skills) / len(preferred_skill_set)
        ) * 100

        preferred_skills_score = round(preferred_skills_score, 2)
        preferred_skills_available = True

        available_components.append((PREFERRED_SKILLS_WEIGHT, preferred_skills_score))
    else:
        matched_preferred_skills = []
        preferred_skills_score = None
        preferred_skills_available = False

    total_weight = sum(weight for weight, _ in available_components)

    weighted_score = sum(weight * score for weight, score in available_components)

    final_score = weighted_score / total_weight

    return FinalMatchResult(
        final_score=round(final_score, 2),
        required_skills_score=required_skills_score,
        experience_score=experience_score,
        projects_score=projects_score,
        qualification_score=qualification_score,
        preferred_skills_score=preferred_skills_score,
        preferred_skills_available=preferred_skills_available,
        matched_required_skills=required_skill_result.matched,
        missing_required_skills=required_skill_result.missing,
        matched_preferred_skills=matched_preferred_skills,
        experience_matches=experience_result.matches,
        project_matches=project_result.matches,
        qualification_matches=qualification_result.matches,
    )
