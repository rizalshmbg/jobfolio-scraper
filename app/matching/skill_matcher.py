from dataclasses import dataclass

from ..job.models import SkillRequirement

# Explicit aliases only. Unknown skills are preserved.
SKILL_ALIASES = {
    "react.js": "react",
    "reactjs": "react",
    "vue.js": "vue",
    "tailwind": "tailwind css",
    "tailwindcss": "tailwind css",
}


def normalize_skill_name(skill: str) -> str:
    """Normalize known skill aliases without fuzzy matching."""
    normalized = " ".join(skill.strip().lower().split())
    return SKILL_ALIASES.get(normalized, normalized)


@dataclass
class SkillMatchResult:
    matched: list[str]
    missing: list[str]
    score: float


def calculate_skill_match(
    resume_skills: list[str],
    required_skills: list[SkillRequirement],
) -> SkillMatchResult:
    required_skills = deduplicate_requirements(required_skills)
    resume_set = {
        normalize_skill_name(skill) for skill in resume_skills if skill.strip()
    }

    if not required_skills:
        return SkillMatchResult(
            matched=[],
            missing=[],
            score=100.0,
        )

    matched: list[str] = []
    missing: list[str] = []

    for requirement in required_skills:
        skills = {
            normalize_skill_name(skill) for skill in requirement.skills if skill.strip()
        }

        if not skills:
            continue

        matched_skills = sorted(resume_set & skills)
        missing_skills = sorted(skills - resume_set)

        if requirement.operator == "OR":
            if matched_skills:
                matched.extend(matched_skills)
            else:
                missing.append(" OR ".join(sorted(skills)))
        else:
            matched.extend(matched_skills)
            missing.extend(missing_skills)

    total_requirements = sum(1 for requirement in required_skills if requirement.skills)

    missing_requirements = count_missing_requirements(
        required_skills,
        resume_set,
    )

    matched_requirements = total_requirements - missing_requirements

    score = (
        (matched_requirements / total_requirements) * 100
        if total_requirements
        else 100.0
    )

    return SkillMatchResult(
        matched=sorted(set(matched)),
        missing=sorted(set(missing)),
        score=round(score, 2),
    )


def count_missing_requirements(
    requirements: list[SkillRequirement],
    resume_set: set[str],
) -> int:
    missing_count = 0

    for requirement in requirements:
        skills = {
            normalize_skill_name(skill) for skill in requirement.skills if skill.strip()
        }

        if not skills:
            continue

        matched_skills = resume_set & skills

        if requirement.operator == "OR":
            if not matched_skills:
                missing_count += 1
        elif skills - resume_set:
            missing_count += 1

    return missing_count


def deduplicate_requirements(
    requirements: list[SkillRequirement],
) -> list[SkillRequirement]:
    """Remove identical requirements after skill normalization."""
    unique_requirements: list[SkillRequirement] = []
    seen: set[tuple[str, tuple[str, ...]]] = set()

    for requirement in requirements:
        normalized_skills = tuple(
            sorted(
                {
                    normalize_skill_name(skill)
                    for skill in requirement.skills
                    if skill.strip()
                }
            )
        )

        if not normalized_skills:
            continue

        key = (requirement.operator, normalized_skills)

        if key in seen:
            continue

        seen.add(key)
        unique_requirements.append(requirement)

    return unique_requirements
