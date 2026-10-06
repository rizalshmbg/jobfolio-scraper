import json

from ..ai.client import GeminiClient
from .models import StructuredResume
from .normalized_models import NormalizedResume

NORMALIZER_PROMPT = """
You are a resume normalization assistant.

Normalize the structured resume below for later semantic job matching.

Return ONLY valid JSON.
Do not use Markdown.
Do not add explanations.

Use exactly this JSON structure:

{{
  "summary": null,
  "skills": [],
  "experience": [
    {{
      "position": null,
      "company": null,
      "startDate": null,
      "endDate": null,
      "location": null,
      "description": []
    }}
  ],
  "education": [
    {{
      "degree": null,
      "institution": null,
      "startDate": null,
      "endDate": null
    }}
  ],
  "projects": [
    {{
      "name": null,
      "startDate": null,
      "endDate": null,
      "description": []
    }}
  ]
}}

Normalization rules:

1. Do not invent skills, experience, education, projects, or facts.
2. Do not remove meaningful information.
3. Normalize skill names into a consistent canonical form.
4. Treat obvious spelling and naming variations as the same skill.
5. Examples:
   - React.js, ReactJS, React JS -> react
   - Node.js, NodeJS, Node JS -> nodejs
   - REST API, RESTful API, RESTful APIs -> rest api
   - TypeScript, Typescript -> typescript
6. Do NOT merge different technologies just because they are related.
7. For example:
   - Java is NOT JavaScript.
   - React is NOT React Native.
   - Vue is NOT Vue Native.
   - Angular is NOT AngularJS.
8. Keep skills as individual items.
9. Do not turn a general concept into a specific technology unless the resume explicitly supports it.
10. Preserve the original meaning of experience and project descriptions.
11. Keep company names, positions, dates, and locations unchanged unless there is an obvious formatting variation.
12. The purpose of normalization is to make later job matching more consistent, not to rewrite the resume.

Structured resume:

---BEGIN STRUCTURED RESUME---

{resume_json}

---END STRUCTURED RESUME---
"""


def normalize_resume_with_ai(
    resume: StructuredResume,
) -> NormalizedResume:
    client = GeminiClient()

    resume_json = resume.model_dump_json()

    prompt = NORMALIZER_PROMPT.format(
        resume_json=resume_json,
    )

    response = client.generate_text(prompt)

    try:
        data = json.loads(response)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Gemini returned invalid JSON for resume normalization"
        ) from exc

    return NormalizedResume.model_validate(data)
