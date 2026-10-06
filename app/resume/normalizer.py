import re

SKILL_ALIASES = {
    "react.js": "react",
    "reactjs": "react",
    "react js": "react",
    "vue.js": "vue",
    "vuejs": "vue",
    "vue js": "vue",
    "next.js": "nextjs",
    "nextjs": "nextjs",
    "node.js": "nodejs",
    "nodejs": "nodejs",
    "javascript": "javascript",
    "js": "javascript",
    "typescript": "typescript",
    "ts": "typescript",
    "css/scss": "css",
    "scss": "scss",
    "rest api": "rest api",
    "restful api": "rest api",
    "restful apis": "rest api",
    "github": "git",
    "git/github": "git",
}


def normalize_skill(
    skill: str,
) -> str:
    value = skill.strip().lower()

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return SKILL_ALIASES.get(
        value,
        value,
    )


def normalize_skills(
    skills: list[str],
) -> list[str]:
    normalized: list[str] = []

    for skill in skills:
        value = normalize_skill(skill)

        if value and value not in normalized:
            normalized.append(value)

    return normalized
