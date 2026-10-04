import re
from typing import Any

from ..normalizer import (
    clean_html_text,
    extract_requirements,
    normalize_employment_type,
    normalize_location,
    normalize_salary,
)
from ..parser import parse_job_posting_json_ld


def clean_text(value: str | None) -> str | None:
    if not value:
        return None

    text = value.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip() or None


def extract_glints_work_arrangement(
    html: str,
) -> str | None:
    match = re.search(
        r'"workArrangementOption"\s*:\s*"(ONSITE|HYBRID|REMOTE)"',
        html,
        re.IGNORECASE,
    )

    if not match:
        return None

    return match.group(1).upper()


def scrape_glints(
    html: str,
    url: str,
) -> dict[str, Any]:
    job_posting = parse_job_posting_json_ld(html)

    if job_posting is None:
        raise ValueError(
            "Unable to parse Glints JobPosting data"
        )

    hiring_organization = job_posting.get(
        "hiringOrganization"
    )

    if isinstance(hiring_organization, dict):
        company = hiring_organization.get("name")
    else:
        company = None

    if not isinstance(company, str):
        company = None

    position = job_posting.get("title")

    if not isinstance(position, str):
        position = None

    description = job_posting.get("description")

    if not isinstance(description, str):
        description = None

    salary_min, salary_max = normalize_salary(
        job_posting.get("baseSalary")
    )

    return {
        "company": clean_text(company),
        "position": clean_text(position),
        "description": clean_html_text(description),
        "requirements": extract_requirements(
            description
        ),
        "jobUrl": url,
        "location": normalize_location(
            job_posting.get("jobLocation")
        ),
        "employmentType": normalize_employment_type(
            job_posting.get("employmentType")
        ),
        "workArrangement": extract_glints_work_arrangement(
            html
        ),
        "salaryMin": salary_min,
        "salaryMax": salary_max,
    }