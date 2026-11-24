import json
import re
from typing import Any

from bs4 import BeautifulSoup

from ...job.models import StructuredJob
from ..normalizer import (
    normalize_employment_type,
    normalize_location,
    normalize_work_arrangement,
)


def find_job_posting(data: Any) -> dict | None:
    if isinstance(data, list):
        for item in data:
            result = find_job_posting(item)
            if result:
                return result

    if not isinstance(data, dict):
        return None

    job_type = data.get("@type")

    if job_type == "JobPosting" or (
        isinstance(job_type, list) and "JobPosting" in job_type
    ):
        return data

    if "@graph" in data:
        return find_job_posting(data["@graph"])

    return None


def extract_job_posting(soup: BeautifulSoup) -> dict:
    for script in soup.find_all(
        "script",
        type="application/ld+json",
    ):
        try:
            data = json.loads(script.string or script.get_text())
        except json.JSONDecodeError, TypeError:
            continue

        job_posting = find_job_posting(data)

        if job_posting:
            return job_posting

    raise ValueError("Dealls job posting data not found")


def extract_section(
    soup: BeautifulSoup,
    heading_text: str,
) -> list[str]:
    for heading in soup.find_all(["h2", "h3"]):
        if heading.get_text(" ", strip=True).lower() != heading_text.lower():
            continue

        section = heading.find_parent("div")

        if not section:
            continue

        items = section.find_all("li")

        return [text for item in items if (text := item.get_text(" ", strip=True))]

    return []


def extract_work_arrangement(
    soup: BeautifulSoup,
) -> str | None:
    job_header = soup.find(id="job-header")

    if not job_header:
        return None

    header_text = job_header.get_text(
        " ",
        strip=True,
    )

    return normalize_work_arrangement(
        job_location_type=None,
        description=header_text,
        html="",
    )


def parse_salary_amount(value: Any) -> int | None:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return int(value)

    if isinstance(value, str):
        digits = re.sub(r"[^\d]", "", value)
        return int(digits) if digits else None

    return None


def extract_salary(
    soup: BeautifulSoup,
    job_data: dict,
) -> tuple[int | None, int | None]:
    # 1. Extract salary from JSON-LD
    base_salary = job_data.get("baseSalary")

    if isinstance(base_salary, dict):
        salary_value = base_salary.get("value")

        if isinstance(salary_value, dict):
            salary_min = parse_salary_amount(salary_value.get("minValue"))
            salary_max = parse_salary_amount(salary_value.get("maxValue"))

            if salary_min is not None or salary_max is not None:
                return salary_min, salary_max

            single_value = parse_salary_amount(salary_value.get("value"))

            if single_value is not None:
                return single_value, single_value

    # 2. Extract salary from visible job header
    job_header = soup.find(id="job-header")

    if not job_header:
        return None, None

    header_text = job_header.get_text(" ", strip=True)

    # Only process text containing an explicit currency marker.
    if not re.search(r"\b(?:Rp|IDR)\b", header_text, re.IGNORECASE):
        return None, None

    amounts = re.findall(
        r"(?:Rp|IDR)\s*([\d.,]+)",
        header_text,
        re.IGNORECASE,
    )

    values = [parse_salary_amount(amount) for amount in amounts]

    values = [value for value in values if value is not None]

    if not values:
        return None, None

    if len(values) == 1:
        return values[0], values[0]

    return values[0], values[1]


def scrape_dealls(
    html: str,
    url: str,
) -> StructuredJob:
    soup = BeautifulSoup(html, "html.parser")

    job_data = extract_job_posting(soup)

    organization = job_data.get("hiringOrganization")

    company = organization.get("name") if isinstance(organization, dict) else None

    responsibilities = extract_section(
        soup,
        "Deskripsi Pekerjaan",
    )

    requirements = extract_section(
        soup,
        "Kualifikasi",
    )

    description = "\n".join(responsibilities) if responsibilities else None

    salary_min, salary_max = extract_salary(
        soup,
        job_data,
    )

    return StructuredJob(
        company=company,
        position=job_data.get("title"),
        description=description,
        requirements=requirements,
        responsibilities=responsibilities,
        jobUrl=url,
        location=normalize_location(job_data.get("jobLocation")),
        employmentType=normalize_employment_type(job_data.get("employmentType")),
        workArrangement=extract_work_arrangement(soup),
        salaryMin=salary_min,
        salaryMax=salary_max,
    )
