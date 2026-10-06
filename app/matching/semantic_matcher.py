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

1. Compare the candidate's projects against the job responsibilities.
2. Use ONLY information explicitly present in the candidate's project name and project descriptions.
3. Do not use information from the candidate's work experience, education, skills, summary, or other projects.
4. Do not invent project experience.
5. Do not assume collaboration with designers, developers, or teams unless the project description explicitly states it.
6. Do not assume backend integration unless the project description explicitly states API/backend integration.
7. Do not assume responsive design unless the project description explicitly supports it.
8. Use relevance values only:
   - HIGH
   - MEDIUM
   - LOW
9. HIGH means the project explicitly demonstrates experience directly relevant to the responsibility.
10. MEDIUM means the project is meaningfully related but does not directly demonstrate the responsibility.
11. LOW means there is only a weak relationship or insufficient evidence.
12. matched must be true when relevance is HIGH or MEDIUM.
13. matched must be false when relevance is LOW.
14. Evidence must quote or closely paraphrase only information from the relevant project.
15. Do not combine evidence from multiple projects into one evidence statement.
16. Do not calculate a numerical score.
17. Do not assume professional employment experience from a project.
18. Consider the project name and project descriptions when determining relevance.

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
