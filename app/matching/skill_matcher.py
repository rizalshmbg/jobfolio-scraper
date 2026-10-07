from dataclasses import dataclass

from ..job.models import SkillRequirement


@dataclass
class SkillMatchResult:
    matched: list[str]
    missing: list[str]
    score: float


def calculate_skill_match(
    resume_skills: list[str],
    required_skills: list[SkillRequirement],
) -> SkillMatchResult:
    resume_set = set(resume_skills)

    if not required_skills:
        return SkillMatchResult(
            matched=[],
            missing=[],
            score=100.0,
        )

    matched: list[str] = []
    missing: list[str] = []

    for requirement in required_skills:
        skills = set(requirement.skills)

        if not skills:
            continue

        if requirement.operator == "OR":
            matched_skills = sorted(resume_set & skills)

            if matched_skills:
                matched.extend(matched_skills)
            else:
                missing.append(" OR ".join(sorted(skills)))

        else:
            matched_skills = sorted(resume_set & skills)
            missing_skills = sorted(skills - resume_set)

            if not missing_skills:
                matched.extend(matched_skills)
            else:
                missing.extend(missing_skills)

    total_requirements = sum(1 for requirement in required_skills if requirement.skills)

    matched_requirements = total_requirements - count_missing_requirements(
        required_skills,
        resume_set,
    )

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
        skills = set(requirement.skills)

        if not skills:
            continue

        matched_skills = resume_set & skills

        if requirement.operator == "OR":
            if not matched_skills:
                missing_count += 1
        else:
            if skills - resume_set:
                missing_count += 1

    return missing_count
