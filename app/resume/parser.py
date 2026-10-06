import re
from typing import Any

SECTION_ALIASES = {
    "summary": {
        "profil",
        "profile",
        "summary",
        "professional summary",
        "about me",
    },
    "education": {
        "pendidikan",
        "education",
        "academic background",
    },
    "skills": {
        "kemampuan",
        "skills",
        "technical skills",
        "technical skills & tools",
        "core skills",
        "technical competencies",
    },
    "experience": {
        "pengalaman kerja",
        "work experience",
        "professional experience",
        "experience",
        "employment history",
    },
    "projects": {
        "projects",
        "project",
        "proyek",
    },
}


def normalize_heading(value: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        value.strip().lower(),
    )


def detect_section_heading(
    line: str,
) -> str | None:
    normalized = normalize_heading(line)

    for section, aliases in SECTION_ALIASES.items():
        if normalized in aliases:
            return section

    return None


def split_sections(
    text: str,
) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}

    current_section: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        section = detect_section_heading(line)

        if section:
            current_section = section
            sections.setdefault(
                current_section,
                [],
            )
            continue

        if current_section:
            sections[current_section].append(line)

    return sections


def clean_bullet(value: str) -> str:
    value = re.sub(
        r"^[•●▪◦*-]\s*",
        "",
        value.strip(),
    )

    return value.rstrip(".").strip()


def parse_skills(
    lines: list[str],
) -> list[str]:
    skills: list[str] = []

    for line in lines:
        value = clean_bullet(line)

        if ":" in value:
            _, value = value.split(
                ":",
                1,
            )

        parts = re.split(
            r"[,;]",
            value,
        )

        for part in parts:
            skill = part.strip()

            if skill and skill not in skills:
                skills.append(skill)

    return skills


def parse_summary(
    lines: list[str],
) -> str | None:
    if not lines:
        return None

    return " ".join(clean_bullet(line) for line in lines).strip() or None


def parse_education(
    lines: list[str],
) -> list[dict[str, Any]]:
    education: list[dict[str, Any]] = []

    text = " ".join(lines)

    date_match = re.search(
        r"(?P<start>\d{2}/\d{4})\s*[–-]\s*(?P<end>\d{2}/\d{4})",
        text,
    )

    date_start = date_match.group("start") if date_match else None

    date_end = date_match.group("end") if date_match else None

    clean_text = re.sub(
        r"\s*\d{2}/\d{4}\s*[–-]\s*\d{2}/\d{4}.*$",
        "",
        text,
    ).strip()

    if clean_text:
        parts = [
            part.strip()
            for part in clean_text.split(
                ",",
                1,
            )
        ]

        degree = parts[0] if parts else None

        institution = parts[1] if len(parts) > 1 else None

        education.append(
            {
                "degree": degree,
                "institution": institution,
                "startDate": date_start,
                "endDate": date_end,
            }
        )

    return education


def parse_experience(
    lines: list[str],
) -> list[dict[str, Any]]:
    experience: list[dict[str, Any]] = []

    current: dict[str, Any] | None = None

    for line in lines:
        value = clean_bullet(line)

        if not value:
            continue

        date_match = re.search(
            r"(?P<start>\d{2}/\d{4})\s*[–-]\s*(?P<end>\d{2}/\d{4})",
            value,
        )

        if date_match and current is None:
            header = value[: date_match.start()].strip()

            header = re.sub(
                r"\s*\|\s*$",
                "",
                header,
            ).strip()

            parts = [
                part.strip()
                for part in header.split(
                    ",",
                    1,
                )
            ]

            company = parts[0] if parts else None

            position = parts[1] if len(parts) > 1 else None

            current = {
                "position": position,
                "company": company,
                "startDate": date_match.group("start"),
                "endDate": date_match.group("end"),
                "location": None,
                "description": [],
            }

            location_match = re.search(
                r"\|\s*(.+)$",
                value,
            )

            if location_match:
                current["location"] = location_match.group(1).strip()

            continue

        if value.startswith(
            (
                "•",
                "●",
                "▪",
                "◦",
                "-",
                "*",
            )
        ):
            if current is not None:
                current["description"].append(clean_bullet(value))

            continue

        if current is not None:
            current["description"].append(value)

    if current is not None:
        experience.append(current)

    return experience


def parse_projects(
    lines: list[str],
) -> list[dict[str, Any]]:
    projects: list[dict[str, Any]] = []

    current: dict[str, Any] | None = None

    for line in lines:
        value = clean_bullet(line)

        if not value:
            continue

        date_match = re.search(
            r"(?P<start>\d{2}/\d{4})\s*[–-]\s*(?P<end>\d{2}/\d{4})",
            value,
        )

        if date_match:
            if current is not None:
                projects.append(current)

            project_name = value[: date_match.start()].strip()

            current = {
                "name": project_name,
                "startDate": date_match.group("start"),
                "endDate": date_match.group("end"),
                "description": [],
            }

            continue

        if current is not None:
            current["description"].append(clean_bullet(value))

    if current is not None:
        projects.append(current)

    return projects


def parse_resume(
    text: str,
) -> dict[str, Any]:
    sections = split_sections(text)

    return {
        "summary": parse_summary(sections.get("summary", [])),
        "skills": parse_skills(sections.get("skills", [])),
        "experience": parse_experience(sections.get("experience", [])),
        "education": parse_education(sections.get("education", [])),
        "projects": parse_projects(sections.get("projects", [])),
    }
