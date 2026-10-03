import json
from typing import Any

from bs4 import BeautifulSoup


def is_job_posting(value: Any) -> bool:
    if not isinstance(value, dict):
        return False

    job_type = value.get("@type")

    if isinstance(job_type, list):
        return "JobPosting" in job_type

    return job_type == "JobPosting"


def find_job_posting(value: Any) -> dict[str, Any] | None:
    if is_job_posting(value):
        return value

    if isinstance(value, list):
        for item in value:
            found = find_job_posting(item)

            if found:
                return found

    if isinstance(value, dict):
        graph = value.get("@graph")

        if isinstance(graph, list):
            for item in graph:
                found = find_job_posting(item)

                if found:
                    return found

    return None


def parse_job_posting_json_ld(
    html: str,
) -> dict[str, Any] | None:
    soup = BeautifulSoup(html, "html.parser")

    scripts = soup.find_all(
        "script",
        attrs={"type": "application/ld+json"},
    )

    for script in scripts:
        content = script.string or script.get_text()

        if not content.strip():
            continue

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            continue

        found = find_job_posting(parsed)

        if found:
            return found

    return None