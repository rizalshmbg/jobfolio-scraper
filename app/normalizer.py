import re
from typing import Any
from bs4 import BeautifulSoup


EMPLOYMENT_TYPE_MAP = {
    "FULL_TIME": "FULL_TIME",
    "FULLTIME": "FULL_TIME",
    "FULL_TIME_EMPLOYEE": "FULL_TIME",
    "PART_TIME": "PART_TIME",
    "PARTTIME": "PART_TIME",
    "CONTRACT": "CONTRACT",
    "CONTRACTOR": "CONTRACT",
    "INTERNSHIP": "INTERNSHIP",
    "INTERN": "INTERNSHIP",
    "FREELANCE": "FREELANCE",
}


def normalize_employment_type(
    employment_type: Any,
) -> str | None:
    if not employment_type:
        return None

    values = (
        employment_type
        if isinstance(employment_type, list)
        else [employment_type]
    )

    for value in values:
        if not isinstance(value, str):
            continue

        normalized = value.strip().upper()
        result = EMPLOYMENT_TYPE_MAP.get(normalized)

        if result:
            return result

    return None


def normalize_location(job_location: Any) -> str | None:
    if not job_location:
        return None

    locations = (
        job_location
        if isinstance(job_location, list)
        else [job_location]
    )

    location = locations[0]

    if not isinstance(location, dict):
        return None

    address = location.get("address")

    if not isinstance(address, dict):
        return None

    country = address.get("addressCountry")

    if isinstance(country, dict):
        country = country.get("name")

    parts = [
        address.get("streetAddress"),
        address.get("addressLocality"),
        address.get("addressRegion"),
        country,
    ]

    parts = [
        value.strip()
        for value in parts
        if isinstance(value, str) and value.strip()
    ]

    return ", ".join(parts) if parts else None


def normalize_salary(
    base_salary: Any,
) -> tuple[int | None, int | None]:
    if not isinstance(base_salary, dict):
        return None, None

    value = base_salary.get("value")

    if not isinstance(value, dict):
        return None, None

    min_value = value.get("minValue")
    max_value = value.get("maxValue")
    single_value = value.get("value")

    salary_min = min_value if min_value is not None else single_value
    salary_max = max_value if max_value is not None else single_value

    return salary_min, salary_max


def extract_requirements(
    description: str | None,
) -> list[str]:
    if not description:
        return []

    soup = BeautifulSoup(description, "html.parser")

    for paragraph in soup.find_all("p"):
        heading = paragraph.get_text(" ", strip=True).lower()

        if "kualifikasi" not in heading:
            continue

        list_element = paragraph.find_next_sibling("ul")

        if not list_element:
            continue

        requirements = []

        for item in list_element.find_all("li"):
            text = item.get_text(" ", strip=True)

            if text:
                requirements.append(text)

        if requirements:
            return requirements

    return []


def normalize_work_arrangement(
    job_location_type: str | None,
    description: str | None,
    html: str,
) -> str | None:
    values = [
        job_location_type,
        description,
        html,
    ]

    values = [
        value
        for value in values
        if isinstance(value, str) and value.strip()
    ]

    if not values:
        return None

    normalized = " ".join(values).lower()
    normalized = normalized.replace("\u00a0", " ")
    normalized = re.sub(r"\s+", " ", normalized)

    if any(
        term in normalized
        for term in [
            "work from home",
            "work-from-home",
            "remote",
            "telecommute",
            "wfh",
            "bekerja dari rumah",
        ]
    ):
        return "REMOTE"

    if any(
        term in normalized
        for term in [
            "hybrid",
            "hybrid working",
            "hybrid work",
        ]
    ):
        return "HYBRID"

    if any(
        term in normalized
        for term in [
            "onsite",
            "on-site",
            "on site",
            "work from office",
            "work-from-office",
            "wfo",
            "bekerja dari kantor",
        ]
    ):
        return "ONSITE"

    return None


def clean_html_text(value: str | None) -> str | None:
    if not value:
        return None

    soup = BeautifulSoup(value, "html.parser")

    for tag in soup.find_all("br"):
        tag.replace_with("\n")

    for tag in soup.find_all(
        ["p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6"]
    ):
        tag.insert_before("\n")
        tag.insert_after("\n")

    text = soup.get_text()

    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip() or None