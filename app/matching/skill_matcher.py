from dataclasses import dataclass


@dataclass
class SkillMatchResult:
    matched: list[str]
    missing: list[str]
    score: float


def calculate_skill_match(
    resume_skills: list[str],
    required_skills: list[str],
) -> SkillMatchResult:
    resume_set = set(resume_skills)
    required_set = set(required_skills)

    if not required_set:
        return SkillMatchResult(
            matched=[],
            missing=[],
            score=100.0,
        )

    matched = sorted(resume_set & required_set)
    missing = sorted(required_set - resume_set)

    score = (
        len(matched) / len(required_set)
    ) * 100

    return SkillMatchResult(
        matched=matched,
        missing=missing,
        score=round(score, 2),
    )