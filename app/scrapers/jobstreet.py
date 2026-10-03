import json
import re
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ..normalizer import (
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
    """
    Keep JobStreet's full HTML description.
    """
    if not content:
        return None

    return content.strip() or None


def extract_requirements(
    content: str | None,
) -> list[str]:
    """
    Extract the requirement list from the
    'About you' section.
    """
    if not content:
        return []

    soup = BeautifulSoup(
        content,
        "html.parser",
    )

    headings = soup.find_all(
        ["p", "h1", "h2", "h3", "h4", "h5", "h6"]
    )

    for heading in headings:
        heading_text = heading.get_text(
            " ",
            strip=True,
        ).lower()

        if heading_text != "about you":
            continue

        # Find the first UL after "About you".
        next_list = heading.find_next("ul")

        if not next_list:
            continue

        requirements: list[str] = []

        for item in next_list.find_all("li"):
            text = clean_text(
                item.get_text(" ", strip=True)
            )

            if text:
                requirements.append(text)

        if requirements:
            return requirements

    return []


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
    job_details: dict[str, Any],
) -> tuple[int | None, int | None]:
    salary = job_details.get("salary")

    if salary is None:
        return None, None

    return normalize_salary(salary)


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
        normalize_jobstreet_salary(
            job_details
        )
    )

    employment_type = None

    # JobStreet's current workTypes for this sample
    # are "Kasual", which does not map safely to the
    # JobFolio employment type enum.
    work_types = job.get("workTypes")

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