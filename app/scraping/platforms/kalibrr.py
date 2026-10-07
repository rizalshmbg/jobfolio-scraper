import re

from bs4 import BeautifulSoup

from ..normalizer import normalize_employment_type


def clean_text(value: str | None) -> str | None:
    if not value:
        return None

    text = value.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip() or None



def extract_position(
    soup: BeautifulSoup,
) -> str | None:
    element = soup.find(
        attrs={"itemprop": "title"}
    )

    if element:
        return clean_text(
            element.get_text(" ", strip=True)
        )

    heading = soup.find("h1")

    if heading:
        return clean_text(
            heading.get_text(" ", strip=True)
        )

    return None


def extract_company(
    soup: BeautifulSoup,
) -> str | None:
    organization = soup.find(
        attrs={
            "itemprop": "hiringOrganization"
        }
    )

    if organization:
        name = organization.find(
            attrs={"itemprop": "name"}
        )

        if name:
            value = name.get("content")

            if isinstance(value, str) and value.strip():
                return clean_text(value)

            return clean_text(
                name.get_text(" ", strip=True)
            )

    heading = soup.find("h2")

    if heading:
        return clean_text(
            heading.get_text(" ", strip=True)
        )

    return None


def extract_description(
    soup: BeautifulSoup,
) -> str | None:
    element = soup.find(
        attrs={"itemprop": "description"}
    )

    if not element:
        return None

    items = element.find_all("li")

    if items:
        return clean_text(
            " ".join(
                item.get_text(" ", strip=True)
                for item in items
            )
        )

    return clean_text(
        element.get_text(" ", strip=True)
    )


def extract_requirements(
    soup: BeautifulSoup,
) -> list[str]:
    element = soup.find(
        attrs={"itemprop": "qualifications"}
    )

    if not element:
        return []

    requirements = []

    for item in element.find_all("li"):
        value = clean_text(
            item.get_text(" ", strip=True)
        )

        if value and value not in requirements:
            requirements.append(value)

    return requirements


def extract_location(
    soup: BeautifulSoup,
) -> str | None:
    job_location = soup.find(
        attrs={"itemprop": "jobLocation"}
    )

    if not job_location:
        return None

    address = job_location.find(
        attrs={"itemprop": "address"}
    )

    if address:
        street = address.find(
            attrs={"itemprop": "streetAddress"}
        )

        if street:
            value = street.get_text(
                " ",
                strip=True,
            )

            if value:
                return clean_text(value)

    return clean_text(
        job_location.get_text(" ", strip=True)
    )



def extract_employment_type(
    soup: BeautifulSoup,
) -> str | None:
    element = soup.find(
        attrs={"itemprop": "employmentType"}
    )

    if not element:
        return None

    value = element.get_text(
        " ",
        strip=True,
    )

    if not value:
        return None

    return normalize_employment_type(value)




def scrape_kalibrr(
    html: str,
    url: str,
) -> dict:
    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    page_text = soup.get_text(
        "\n",
        strip=True,
    )

    return {
        "company": extract_company(soup),
        "position": extract_position(soup),
        "description": extract_description(
            soup,
        ),
        "requirements": extract_requirements(
            soup,
        ),
        "jobUrl": url,
        "location": extract_location(soup),
        "employmentType": extract_employment_type(
            soup,
        ),
        "workArrangement": None,
        "salaryMin": None,
        "salaryMax": None,
    }