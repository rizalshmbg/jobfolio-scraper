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
11. Every match must include a non-empty evidence array.

12. For HIGH relevance, evidence must identify specific information
    from the candidate's experience that directly supports the match.

13. For MEDIUM relevance, evidence must identify specific information
    from the candidate's experience that supports the partial match.

14. For LOW relevance, evidence must briefly explain why the provided
    experience does not sufficiently support the responsibility.

15. Evidence must be based only on the candidate experience provided
    in the input.

16. Do not invent experience, skills, technologies, or facts.

17. If information is missing, describe only what cannot be established
    from the provided data. Do not claim that the candidate lacks a
    capability merely because it is not mentioned in the resume.

18. Evidence must be a list of concise strings, not an empty list.

19. Do not calculate a numerical score.

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

10. Assign HIGH when the project explicitly demonstrates the main
    activity described in the responsibility, or a very close
    semantic equivalent, with specific supporting evidence.

11. Assign MEDIUM when the project explicitly supports a meaningful
    part of a responsibility, but does not demonstrate the main
    activity sufficiently for HIGH relevance.

12. A responsibility may contain multiple activities or criteria.
    Evaluate the overall relevance based on the evidence available
    for the responsibility as a whole.

13. Do not automatically assign LOW merely because one activity
    within a combined responsibility is not documented, when other
    explicitly documented activities are meaningfully relevant.

14. Do not assign HIGH merely because the project uses the same
    technology mentioned in the responsibility. The project must
    also provide evidence of the relevant activity.

15. Assign LOW when the project provides only a weak relationship
    or insufficient evidence of meaningful relevance.

16. Do not assume that missing information means the candidate
    cannot perform the activity.

17. Use relevance values only:
    - HIGH
    - MEDIUM
    - LOW

18. matched must be true when relevance is HIGH or MEDIUM.

19. matched must be false when relevance is LOW.

20. Evidence must be based ONLY on the relevant project.

21. Evidence must briefly explain the connection between the project
    and the responsibility.

22. Evidence must not contain information that is not present in the
    project.

23. Do not combine evidence from multiple projects into one evidence
    statement.

24. Do not assume professional employment experience from a project.

25. Do not assume collaboration with designers, developers, or teams
    unless explicitly stated in the project.

26. Do not assume backend development unless explicitly stated.

27. However, explicit API integration, API consumption, fetching data
    from APIs, sending data through APIs, or similar API-related
    project descriptions are valid evidence for responsibilities
    involving API integration.

28. Do not assume responsive design unless explicitly supported by the
    project description.

29. Consider both the project name and project description.

30. Do not calculate a numerical score.

31. Every match must include a non-empty evidence array.

32. For HIGH or MEDIUM relevance, evidence must identify specific
    information in the relevant project that supports the match.

33. For LOW relevance, evidence must briefly explain why the provided
    project information does not sufficiently support the responsibility.

34. Do not invent project details or candidate capabilities.

35. If information is missing, describe only what cannot be established
    from the provided project data. Do not claim that the candidate
    lacks a capability merely because it is not mentioned.

36. Evidence must be a list of concise strings, not an empty list.

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
