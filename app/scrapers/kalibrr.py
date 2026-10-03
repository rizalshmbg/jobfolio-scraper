import json
import re

from bs4 import BeautifulSoup

from ..normalizer import normalize_employment_type


def clean_text(value: str | None) -> str | None:
    if not value:
        return None

    text = value.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip() or None


def extract_json_ld_job(html: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")

    for script in soup.find_all(
        "script",
        attrs={"type": "application/ld+json"},
    ):
        content = script.string or script.get_text()

        if not content.strip():
            continue

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            continue

        items = (
            parsed
            if isinstance(parsed, list)
            else [parsed]
        )

        for item in items:
            if not isinstance(item, dict):
                continue

            if item.get("@type") == "JobPosting":
                return item

    return None


def extract_position(
    soup: BeautifulSoup,
    job_data: dict | None,
) -> str | None:
    if job_data:
        title = job_data.get("title")

        if isinstance(title, str) and title.strip():
            return clean_text(title)

    heading = soup.find("h1")

    if heading:
        return clean_text(
            heading.get_text(" ", strip=True)
        )

    return None


def extract_company(
    soup: BeautifulSoup,
    job_data: dict | None,
) -> str | None:
    if job_data:
        organization = job_data.get(
            "hiringOrganization"
        )

        if isinstance(organization, dict):
            name = organization.get("name")

            if isinstance(name, str) and name.strip():
                return clean_text(name)

    page_text = soup.get_text(
        "\n",
        strip=True,
    )

    match = re.search(
        r"(PT\s+[A-Z][^\n]+)",
        page_text,
    )

    if match:
        return clean_text(match.group(1))

    return None


def extract_description(
    page_text: str,
) -> str | None:
    match = re.search(
        r"What are the Job Descriptions for this position\? \(Responsibilities\)"
        r"(.*?)(?=Kualifikasi Minimum)",
        page_text,
        re.IGNORECASE | re.DOTALL,
    )

    if not match:
        return None

    section = match.group(1)

    # Remove duplicate content.
    lines = [
        clean_text(line)
        for line in section.splitlines()
    ]

    lines = [
        line
        for line in lines
        if line
    ]

    unique_lines = []

    for line in lines:
        if line not in unique_lines:
            unique_lines.append(line)

    text = " ".join(unique_lines)

    # Remove duplicated paragraph if the same
    # responsibility block appears twice.
    half = len(text) // 2

    if (
        half > 0
        and text[:half].strip()
        == text[half:].strip()
    ):
        text = text[:half].strip()

    return clean_text(text)


def extract_requirements(
    page_text: str,
) -> list[str]:
    match = re.search(
        r"Kualifikasi Minimum"
        r"(.*?)(?=Ringkasan Perkerjaan|Ringkasan Pekerjaan|$)",
        page_text,
        re.IGNORECASE | re.DOTALL,
    )

    if not match:
        return []

    section = match.group(1)

    # Remove duplicated section.
    section = re.sub(
        r"(A\. Primary Qualifications.*)"
        r"\1",
        r"\1",
        section,
        flags=re.IGNORECASE | re.DOTALL,
    )

    requirements = []

    # Education
    education = re.search(
        r"1\.\s*Education:\s*(.*?)(?=2\.\s*Experience:)",
        section,
        re.IGNORECASE | re.DOTALL,
    )

    if education:
        value = clean_text(education.group(1))

        if value:
            requirements.append(
                f"Education: {value}"
            )

    # Experience
    experience = re.search(
        r"2\.\s*Experience:\s*(.*?)(?=3\.\s*Skills:)",
        section,
        re.IGNORECASE | re.DOTALL,
    )

    if experience:
        value = clean_text(experience.group(1))

        if value:
            requirements.append(
                f"Experience: {value}"
            )

    # Skills
    skills = re.search(
        r"3\.\s*Skills:\s*(.*?)(?=4\.\s*Interpersonal and Communication skills)",
        section,
        re.IGNORECASE | re.DOTALL,
    )

    if skills:
        skills_text = skills.group(1)

        skill_items = re.findall(
            r"•\s*(.*?)(?=•|$)",
            skills_text,
            re.DOTALL,
        )

        if skill_items:
            for item in skill_items:
                value = clean_text(item)

                if value:
                    requirements.append(value)
        else:
            value = clean_text(skills_text)

            if value:
                requirements.append(
                    f"Skills: {value}"
                )

    # Communication
    communication = re.search(
        r"4\.\s*Interpersonal and Communication skills\s*(.*?)(?=Ringkasan Perkerjaan|Ringkasan Pekerjaan|$)",
        section,
        re.IGNORECASE | re.DOTALL,
    )

    if communication:
        communication_text = communication.group(1)

        items = re.findall(
            r"•\s*(.*?)(?=•|$)",
            communication_text,
            re.DOTALL,
        )

        if items:
            for item in items:
                value = clean_text(item)

                if value:
                    requirements.append(value)
        else:
            value = clean_text(communication_text)

            if value:
                requirements.append(value)

    # Remove duplicates while preserving order.
    unique_requirements = []

    for requirement in requirements:
        if requirement not in unique_requirements:
            unique_requirements.append(requirement)

    return unique_requirements


def extract_location(
    page_text: str,
) -> str | None:
    match = re.search(
        r"(Kota [^\n]+,\s*Indonesia)",
        page_text,
        re.IGNORECASE,
    )

    if match:
        return clean_text(match.group(1))

    return None


def extract_employment_type(
    page_text: str,
) -> str | None:
    if re.search(
        r"\bFULL[_ ]TIME\b|\bFull time\b",
        page_text,
        re.IGNORECASE,
    ):
        return normalize_employment_type(
            "FULL_TIME"
        )

    if re.search(
        r"\bPART[_ ]TIME\b|\bPart time\b",
        page_text,
        re.IGNORECASE,
    ):
        return normalize_employment_type(
            "PART_TIME"
        )

    if re.search(
        r"\bCONTRACT\b",
        page_text,
        re.IGNORECASE,
    ):
        return normalize_employment_type(
            "CONTRACT"
        )

    if re.search(
        r"\bINTERNSHIP\b|\bIntern\b",
        page_text,
        re.IGNORECASE,
    ):
        return normalize_employment_type(
            "INTERNSHIP"
        )

    if re.search(
        r"\bFREELANCE\b",
        page_text,
        re.IGNORECASE,
    ):
        return normalize_employment_type(
            "FREELANCE"
        )

    return None




def scrape_kalibrr(
    html: str,
    url: str,
) -> dict:
    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    job_data = extract_json_ld_job(html)

    page_text = soup.get_text(
        "\n",
        strip=True,
    )

    return {
        "company": extract_company(
            soup,
            job_data,
        ),
        "position": extract_position(
            soup,
            job_data,
        ),
        "description": extract_description(
            page_text,
        ),
        "requirements": extract_requirements(
            page_text,
        ),
        "jobUrl": url,
        "location": extract_location(
            page_text,
        ),
        "employmentType": extract_employment_type(
            page_text,
        ),
        "workArrangement": None,
        "salaryMin": None,
        "salaryMax": None,
    }