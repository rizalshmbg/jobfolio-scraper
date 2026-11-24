import json
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


def extract_work_arrangement(soup: BeautifulSoup) -> str | None:
    job_header = soup.find(id="job-header")

    if not job_header:
        return None

    header_text = job_header.get_text(" ", strip=True)

    return normalize_work_arrangement(
        job_location_type=None,
        description=header_text,
        html="",
    )


def scrape_dealls(html: str, url: str) -> StructuredJob:
    soup = BeautifulSoup(html, "html.parser")

    job_data = extract_job_posting(soup)

    organization = job_data.get("hiringOrganization")
    company = organization.get("name") if isinstance(organization, dict) else None

    responsibilities = extract_section(
        soup,
        "Deskripsi Pekerjaan",
    )

    qualifications = extract_section(
        soup,
        "Kualifikasi",
    )

    description = "\n".join(responsibilities) or None

    return StructuredJob(
        title=job_data.get("title"),
        company=company,
        description=description,
        location=normalize_location(job_data.get("jobLocation")),
        employmentType=normalize_employment_type(job_data.get("employmentType")),
        workArrangement=extract_work_arrangement(soup),
        responsibilities=responsibilities,
        qualifications=qualifications,
    )
