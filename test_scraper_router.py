from app.scrapers import detect_platform


def assert_equal(name: str, actual, expected):
    if actual != expected:
        raise AssertionError(
            f"{name}: expected {expected!r}, got {actual!r}"
        )

    print(f"✓ {name}")


def main():
    print("=== TEST SCRAPER ROUTER ===\n")

    assert_equal(
        "JobStreet",
        detect_platform(
            "https://id.jobstreet.com/id/job/95017558"
        ),
        "jobstreet",
    )

    assert_equal(
        "Kalibrr",
        detect_platform(
            "https://www.kalibrr.id/id-ID/c/wfveagezndntcyt/jobs/271840/frontend-engineer"
        ),
        "kalibrr",
    )

    assert_equal(
        "Glints",
        detect_platform(
            "https://glints.com/id/opportunities/jobs/web-developer/a1af4101-c328-4280-b87c-ea2326f3743e"
        ),
        "glints",
    )

    assert_equal(
        "Generic",
        detect_platform(
            "https://example.com/jobs/frontend-engineer"
        ),
        "generic",
    )

    print("\nScraper router: PASS")


if __name__ == "__main__":
    main()