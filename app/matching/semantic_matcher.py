import json

from ..ai.client import GeminiClient
from .models import ExperienceMatchResult

EXPERIENCE_MATCH_PROMPT = """
You are a semantic job matching assistant.

Compare the candidate's experience with the job responsibilities.

Return ONLY valid JSON.
Do not use Markdown.
Do not add explanations.

Use exactly this structure:

{{
  "matches": [
    {{
      "matched": true,
      "relevance": "HIGH",
      "evidence": []
    }}
  ]
}}

Rules:

1. Compare the candidate experience against the job responsibilities.
2. Use only information explicitly present in the candidate experience.
3. Do not invent experience.
4. Do not infer a technology unless it is supported by the candidate's experience.
5. Use relevance values only:
   - HIGH
   - MEDIUM
   - LOW
6. HIGH means the candidate experience directly matches the responsibility.
7. MEDIUM means the candidate experience is meaningfully related but not a direct match.
8. LOW means there is only a weak relationship.
9. matched must be true when relevance is HIGH or MEDIUM.
10. matched must be false when relevance is LOW.
11. Evidence must briefly explain why the experience is relevant.
12. Do not calculate a numerical score.

Candidate experience:

---BEGIN EXPERIENCE---

{experience_json}

---END EXPERIENCE---

Job responsibilities:

---BEGIN RESPONSIBILITIES---

{responsibilities_json}

---END RESPONSIBILITIES---
"""


RELEVANCE_SCORES = {
    "HIGH": 1.0,
    "MEDIUM": 0.5,
    "LOW": 0.0,
}


def calculate_experience_match(
    experience: list[dict],
    responsibilities: list[str],
) -> ExperienceMatchResult:
    if not responsibilities:
        return ExperienceMatchResult(
            score=100.0,
            matches=[],
        )

    client = GeminiClient()

    experience_json = json.dumps(
        experience,
        ensure_ascii=False,
        indent=2,
    )

    responsibilities_json = json.dumps(
        responsibilities,
        ensure_ascii=False,
        indent=2,
    )

    prompt = EXPERIENCE_MATCH_PROMPT.format(
        experience_json=experience_json,
        responsibilities_json=responsibilities_json,
    )

    response = client.generate_text(prompt)

    try:
        data = json.loads(response)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Gemini returned invalid JSON for experience matching"
        ) from exc

    matches = data.get("matches", [])

    if len(matches) != len(responsibilities):
        raise ValueError("Gemini returned an incorrect number of experience matches")

    total = 0.0

    for match in matches:
        relevance = match.get("relevance", "LOW").upper()

        if relevance not in RELEVANCE_SCORES:
            raise ValueError(f"Invalid relevance value: {relevance}")

        match["relevance"] = relevance
        match["matched"] = relevance != "LOW"

        total += RELEVANCE_SCORES[relevance]

    score = (total / len(responsibilities)) * 100

    return ExperienceMatchResult(
        score=round(score, 2),
        matches=matches,
    )


PROJECT_MATCH_PROMPT = """
You are a semantic job matching assistant.

Compare the candidate's projects with the job responsibilities.

Return ONLY valid JSON.
Do not use Markdown.
Do not add explanations.

Use exactly this structure:

{{
  "matches": [
    {{
      "matched": true,
      "relevance": "HIGH",
      "evidence": []
    }}
  ]
}}

Rules:

1. Compare each job responsibility against the candidate's projects.

2. The output must contain exactly one match for each job responsibility,
   in the same order as the responsibilities.

3. Use ONLY information explicitly present in the candidate's project
   name and project descriptions.

4. Do not use information from:
   - candidate work experience
   - candidate education
   - candidate skills
   - candidate summary
   - other projects

5. Do not invent project experience.

6. Do not assume a technology, responsibility, or capability unless
   the project information provides explicit evidence.

7. Identify direct semantic relationships between the project
   description and the job responsibility.

8. Pay attention to equivalent wording and closely related concepts.

   Examples:

   - "integrated APIs"
     is directly relevant to
     "API integration"

   - "fetch and display dynamic data"
     is relevant to
     "integrating APIs for dynamic data"

   - "responsive user interface"
     is relevant to
     "developing responsive interfaces"

   - "fixed bugs"
     is relevant to
     "bug fixing"

   - "improved performance"
     is relevant to
     "performance improvement"

9. Do not require the wording to be identical.

10. A project can receive HIGH relevance when the project description
    explicitly demonstrates the same responsibility or a very close
    equivalent.

11. Use MEDIUM when the project is meaningfully related to the
    responsibility but does not explicitly demonstrate the full
    responsibility.

12. Use LOW when:
    - there is only a weak relationship, or
    - the project does not provide sufficient evidence.

13. Use relevance values only:
    - HIGH
    - MEDIUM
    - LOW

14. matched must be true when relevance is HIGH or MEDIUM.

15. matched must be false when relevance is LOW.

16. Evidence must be based ONLY on the relevant project.

17. Evidence must briefly explain the connection between the project
    and the responsibility.

18. Evidence must not contain information that is not present in the
    project.

19. Do not combine evidence from multiple projects into one evidence
    statement.

20. Do not assume professional employment experience from a project.

21. Do not assume collaboration with designers, developers, or teams
    unless explicitly stated in the project.

22. Do not assume backend development unless explicitly stated.

23. However, explicit API integration, API consumption, fetching data
    from APIs, sending data through APIs, or similar API-related
    project descriptions are valid evidence for responsibilities
    involving API integration.

24. Do not assume responsive design unless explicitly supported by the
    project description.

25. Consider both the project name and project description.

26. Do not calculate a numerical score.

Candidate projects:

---BEGIN PROJECTS---

{projects_json}

---END PROJECTS---

Job responsibilities:

---BEGIN RESPONSIBILITIES---

{responsibilities_json}

---END RESPONSIBILITIES---
"""


def calculate_project_match(
    projects: list[dict],
    responsibilities: list[str],
) -> ExperienceMatchResult:
    if not responsibilities:
        return ExperienceMatchResult(
            score=100.0,
            matches=[],
        )

    client = GeminiClient()

    projects_json = json.dumps(
        projects,
        ensure_ascii=False,
        indent=2,
    )

    responsibilities_json = json.dumps(
        responsibilities,
        ensure_ascii=False,
        indent=2,
    )

    prompt = PROJECT_MATCH_PROMPT.format(
        projects_json=projects_json,
        responsibilities_json=responsibilities_json,
    )

    response = client.generate_text(prompt)

    try:
        data = json.loads(response)
    except json.JSONDecodeError as exc:
        raise ValueError("Gemini returned invalid JSON for project matching") from exc

    matches = data.get("matches", [])

    if len(matches) != len(responsibilities):
        raise ValueError("Gemini returned an incorrect number of project matches")

    total = 0.0

    for match in matches:
        relevance = match.get("relevance", "LOW").upper()

        if relevance not in RELEVANCE_SCORES:
            raise ValueError(f"Invalid relevance value: {relevance}")

        match["relevance"] = relevance
        match["matched"] = relevance != "LOW"

        total += RELEVANCE_SCORES[relevance]

    score = (total / len(responsibilities)) * 100

    return ExperienceMatchResult(
        score=round(score, 2),
        matches=matches,
    )
