import json
import re
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ..normalizer import (
    clean_html_text,
    normalize_employment_type,
    normalize_salary,
)


def extract_window_assignment(
    html: str,
    variable_name: str,
) -> str | None:
    """
    Extract a complete window.<VARIABLE>={...} assignment
    from JobStreet HTML.

    A simple regex is not enough because the JSON can contain
    semicolons and nested objects.
    """
    pattern = re.compile(
        rf"window\.{re.escape(variable_name)}\s*="
    )

    match = pattern.search(html)

    if not match:
        return None

    value_start = match.end()

    while (
        value_start < len(html)
        and html[value_start].isspace()
    ):
        value_start += 1

    if value_start >= len(html):
        return None

    if html[value_start] != "{":
        return None

    depth = 0
    in_string = False
    escape = False

    for index in range(value_start, len(html)):
        char = html[index]

        if in_string:
            if escape:
                escape = False
                continue

            if char == "\\":
                escape = True
                continue

            if char == '"':
                in_string = False

            continue

        if char == '"':
            in_string = True
            continue

        if char == "{":
            depth += 1
            continue

        if char == "}":
            depth -= 1

            if depth == 0:
                return html[value_start:index + 1]

    return None


def parse_redux_data(html: str) -> dict[str, Any] | None:
    """
    Parse JobStreet SEEK_REDUX_DATA.
    """
    raw = extract_window_assignment(
        html,
        "SEEK_REDUX_DATA",
    )

    if not raw:
        return None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None

    if not isinstance(data, dict):
        return None

    return data

def find_job_details(
    value: Any,
) -> dict[str, Any] | None:
    """
    Recursively find the JobDetails object that contains
    a Job object.
    """
    if isinstance(value, dict):
        job = value.get("job")

        if isinstance(job, dict):
            if (
                isinstance(job.get("title"), str)
                or isinstance(job.get("id"), str)
            ):
                return value

        for child in value.values():
            found = find_job_details(child)

            if found:
                return found

    elif isinstance(value, list):
        for child in value:
            found = find_job_details(child)

            if found:
                return found

    return None


def get_job_details(
    redux_data: dict[str, Any],
) -> dict[str, Any] | None:
    """
    Find the JobDetails object from SEEK_REDUX_DATA.
    """
    return find_job_details(redux_data)


def clean_text(value: str | None) -> str | None:
    if not value:
        return None

    text = BeautifulSoup(
        value,
        "html.parser",
    ).get_text(" ", strip=True)

    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip() or None


def extract_description(
    content: str | None,
) -> str | None:
    if not content:
        return None

    return clean_html_text(content)


def extract_requirements(
    content: str | None,
) -> list[str]:
    """
    Extract requirements from JobStreet requirement sections.

    Supported sections include:
    - About you
    - Kemampuan Teknis
    - Kualifikasi
    - Qualifications
    - Requirements
    """
    if not content:
        return []

    soup = BeautifulSoup(
        content,
        "html.parser",
    )

    requirement_heading_patterns = [
        "about you",
        "kemampuan teknis",
        "kualifikasi",
        "qualifications",
        "requirements",
        "requirement",
    ]

    headings = soup.find_all(
        ["p", "h1", "h2", "h3", "h4", "h5", "h6"]
    )

    requirements: list[str] = []
    seen: set[str] = set()

    for heading in headings:
        heading_text = heading.get_text(
            " ",
            strip=True,
        ).lower()

        is_requirement_section = any(
            heading_text == pattern
            or heading_text.startswith(pattern)
            for pattern in requirement_heading_patterns
        )

        if not is_requirement_section:
            continue

        next_list = heading.find_next("ul")

        if not next_list:
            continue

        for item in next_list.find_all("li"):
            text = clean_text(
                item.get_text(" ", strip=True)
            )

            if not text:
                continue

            if text in seen:
                continue

            seen.add(text)
            requirements.append(text)

    return requirements


def normalize_jobstreet_work_arrangement(
    job_details: dict[str, Any],
) -> str | None:
    work_arrangements = job_details.get(
        "workArrangements"
    )

    if not isinstance(work_arrangements, dict):
        return None

    arrangements = work_arrangements.get(
        "arrangements"
    )

    if not isinstance(arrangements, list):
        return None

    for arrangement in arrangements:
        if not isinstance(arrangement, dict):
            continue

        arrangement_type = arrangement.get("type")

        if arrangement_type in {
            "ONSITE",
            "HYBRID",
            "REMOTE",
        }:
            return arrangement_type

    return None


def normalize_jobstreet_location(
    job: dict[str, Any],
    job_details: dict[str, Any],
) -> str | None:
    location = job.get("location")

    if not isinstance(location, dict):
        location = job_details.get("location")

    if not isinstance(location, dict):
        return None

    label = location.get("label")

    if not isinstance(label, str):
        return None

    return clean_text(label)


def normalize_jobstreet_company(
    job: dict[str, Any],
    job_details: dict[str, Any],
) -> str | None:
    advertiser = job.get("advertiser")

    if not isinstance(advertiser, dict):
        advertiser = job_details.get("advertiser")

    if not isinstance(advertiser, dict):
        return None

    name = advertiser.get("name")

    if not isinstance(name, str):
        return None

    return clean_text(name)


def normalize_jobstreet_salary(
    job: dict[str, Any],
) -> tuple[int | None, int | None]:
    salary = job.get("salary")

    if not isinstance(salary, dict):
        return None, None

    label = salary.get("label")

    if not isinstance(label, str):
        return None, None

    values = re.findall(
        r"Rp\s*([\d.]+)",
        label,
    )

    if not values:
        return None, None

    numbers = [
        int(value.replace(".", ""))
        for value in values
    ]

    if len(numbers) == 1:
        return numbers[0], numbers[0]

    return numbers[0], numbers[1]


def scrape_jobstreet(
    html: str,
    url: str,
) -> dict[str, Any]:
    """
    Scrape a JobStreet job detail page.
    """
    redux_data = parse_redux_data(html)

    if redux_data is None:
        raise ValueError(
            "Unable to parse JobStreet page data"
        )

    job_details = get_job_details(redux_data)

    if job_details is None:
        raise ValueError(
            "Unable to find JobStreet job details"
        )

    job = job_details.get("job")

    if not isinstance(job, dict):
        raise ValueError(
            "Unable to find JobStreet job"
        )

    position = job.get("title")

    if not isinstance(position, str):
        position = None

    content = job.get("content2")

    if not isinstance(content, str):
        content = job.get("content")

    if not isinstance(content, str):
        content = None

    salary_min, salary_max = (
        normalize_jobstreet_salary(job)
    )

    employment_type = None

    work_types = job.get("workTypes")

    if not isinstance(work_types, dict):
        work_types = job_details.get("workTypes")

    if isinstance(work_types, dict):
        label = work_types.get("label")

        if isinstance(label, str):
            employment_type = (
                normalize_employment_type(label)
            )

    return {
        "company": normalize_jobstreet_company(
            job,
            job_details,
        ),
        "position": position,
        "description": extract_description(
            content
        ),
        "requirements": extract_requirements(
            content
        ),
        "jobUrl": url,
        "location": normalize_jobstreet_location(
            job,
            job_details,
        ),
        "employmentType": employment_type,
        "workArrangement": (
            normalize_jobstreet_work_arrangement(
                job_details
            )
        ),
        "salaryMin": salary_min,
        "salaryMax": salary_max,
    }