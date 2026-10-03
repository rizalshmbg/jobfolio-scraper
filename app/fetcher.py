import ipaddress
import socket
from urllib.parse import urlparse

import httpx


FETCH_TIMEOUT = 10.0
MAX_RESPONSE_SIZE = 2 * 1024 * 1024


def is_private_ip(ip: str) -> bool:
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return False

    return (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_unspecified
    )


def validate_target_url(url_string: str) -> str:
    parsed = urlparse(url_string)

    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Job URL must use HTTP or HTTPS")

    hostname = parsed.hostname

    if not hostname:
        raise ValueError("Invalid job URL")

    hostname = hostname.lower()

    if (
        hostname == "localhost"
        or hostname.endswith(".localhost")
        or hostname in {"127.0.0.1", "0.0.0.0", "::1"}
    ):
        raise ValueError("Job URL is not allowed")

    try:
        addresses = socket.getaddrinfo(
            hostname,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        raise ValueError("Unable to resolve job URL") from exc

    if not addresses:
        raise ValueError("Unable to resolve job URL")

    for address in addresses:
        ip = address[4][0]

        if is_private_ip(ip):
            raise ValueError("Job URL is not allowed")

    return url_string


async def fetch_job_page(url: str) -> str:
    validate_target_url(url)

    headers = {
        "User-Agent": "JobFolio/1.0",
        "Accept": "text/html,application/xhtml+xml",
    }

    timeout = httpx.Timeout(FETCH_TIMEOUT)

    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=False,
            headers=headers,
        ) as client:
            response = await client.get(url)

    except httpx.TimeoutException as exc:
        raise TimeoutError("Job page request timed out") from exc

    except httpx.HTTPError as exc:
        raise ValueError("Unable to fetch job page") from exc

    cloudflare_mitigation = response.headers.get("cf-mitigated")

    if (
        response.status_code == 403
        and cloudflare_mitigation == "challenge"
    ):
        raise PermissionError(
            "This website requires a security verification "
            "before the job page can be imported."
        )

    if response.status_code < 200 or response.status_code >= 300:
        raise ValueError(
            f"Unable to fetch job page ({response.status_code})"
        )

    content_type = response.headers.get("content-type", "")

    if "text/html" not in content_type:
        raise ValueError("Job URL must return an HTML page")

    content_length = response.headers.get("content-length")

    if content_length:
        try:
            if int(content_length) > MAX_RESPONSE_SIZE:
                raise ValueError("Job page is too large")
        except ValueError as exc:
            if str(exc) == "Job page is too large":
                raise
            # Ignore malformed Content-Length.

    body = response.text

    if len(body.encode("utf-8")) > MAX_RESPONSE_SIZE:
        raise ValueError("Job page is too large")

    return body