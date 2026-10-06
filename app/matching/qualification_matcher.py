import json

from ..ai.client import GeminiClient
from .models import ExperienceMatchResult

QUALIFICATION_MATCH_PROMPT = """
You are a qualification matching assistant.

Compare each job qualification against the candidate's resume information.

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

1. Evaluate each job qualification separately.
2. Use only information explicitly present in the candidate resume data.
3. Do not invent candidate qualifications.
4. Use relevance values only:
   - HIGH
   - MEDIUM
   - LOW
5. HIGH means the candidate clearly satisfies the qualification based on explicit evidence.
6. MEDIUM means the candidate has strong related evidence, but the qualification itself is not explicitly stated or fully demonstrated.
7. LOW means there is insufficient evidence that the candidate satisfies the qualification.
8. matched must be true when relevance is HIGH or MEDIUM.
9. matched must be false when relevance is LOW.
10. Evidence must briefly explain why the candidate matches.
11. Do not calculate a numerical score.
12. For education qualifications, use the candidate's education data.
13. For experience or practical knowledge qualifications, use the candidate's experience and project data.
14. Do not use information from unrelated resume fields when evaluating a qualification.
15. Do not assume a qualification merely because it is common for the candidate's job title.
16. Do not treat related experience as proof of a qualification when the qualification requires a specific level of knowledge, proficiency, certification, or condition.
17. For example, experience building responsive interfaces may support "responsive web design knowledge", but should not automatically be treated as explicit proof of "good understanding".
18. Evidence must distinguish between explicit qualification evidence and related supporting evidence.

Candidate education:

---BEGIN EDUCATION---

{education_json}

---END EDUCATION---

Candidate experience:

---BEGIN EXPERIENCE---

{experience_json}

---END EXPERIENCE---

Candidate projects:

---BEGIN PROJECTS---

{projects_json}

---END PROJECTS---

Job qualifications:

---BEGIN QUALIFICATIONS---

{qualifications_json}

---END QUALIFICATIONS---
"""


RELEVANCE_SCORES = {
    "HIGH": 1.0,
    "MEDIUM": 0.5,
    "LOW": 0.0,
}


def calculate_qualification_match(
    education: list[dict],
    experience: list[dict],
    projects: list[dict],
    qualifications: list[str],
) -> ExperienceMatchResult:

    if not qualifications:
        return ExperienceMatchResult(
            score=100.0,
            matches=[],
        )

    client = GeminiClient()

    education_json = json.dumps(
        education,
        ensure_ascii=False,
        indent=2,
    )

    experience_json = json.dumps(
        experience,
        ensure_ascii=False,
        indent=2,
    )

    projects_json = json.dumps(
        projects,
        ensure_ascii=False,
        indent=2,
    )

    qualifications_json = json.dumps(
        qualifications,
        ensure_ascii=False,
        indent=2,
    )

    prompt = QUALIFICATION_MATCH_PROMPT.format(
        education_json=education_json,
        experience_json=experience_json,
        projects_json=projects_json,
        qualifications_json=qualifications_json,
    )

    response = client.generate_text(prompt)

    try:
        data = json.loads(response)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Gemini returned invalid JSON for qualification matching"
        ) from exc

    matches = data.get("matches", [])

    if len(matches) != len(qualifications):
        raise ValueError("Gemini returned an incorrect number of qualification matches")

    total = 0.0

    for match in matches:
        relevance = match.get(
            "relevance",
            "LOW",
        ).upper()

        if relevance not in RELEVANCE_SCORES:
            raise ValueError(f"Invalid relevance value: {relevance}")

        match["relevance"] = relevance
        match["matched"] = relevance != "LOW"

        total += RELEVANCE_SCORES[relevance]

    score = (total / len(qualifications)) * 100

    return ExperienceMatchResult(
        score=round(score, 2),
        matches=matches,
    )
