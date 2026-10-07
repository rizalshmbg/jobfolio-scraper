from urllib.parse import urlparse

from .glints import scrape_glints
from .jobstreet import scrape_jobstreet
from .kalibrr import scrape_kalibrr


def detect_platform(url: str) -> str:
    hostname = urlparse(url).hostname or ""
    hostname = hostname.lower()

    if "kalibrr" in hostname:
        return "kalibrr"

    if "glints" in hostname:
        return "glints"

    if "jobstreet" in hostname:
        return "jobstreet"

    return "generic"


def scrape_by_platform(
    html: str,
    url: str,
) -> dict:
    platform = detect_platform(url)

    if platform == "kalibrr":
        return scrape_kalibrr(html, url)

    if platform == "jobstreet":
        return scrape_jobstreet(html, url)

    if platform == "glints":
        return scrape_glints(html, url)

    raise ValueError(
        f"Unsupported scraper platform: {platform}"
    )