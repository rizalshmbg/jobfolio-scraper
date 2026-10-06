import json

from ..ai.client import GeminiClient
from .models import StructuredResume

RESUME_PROMPT = """
You are a resume parsing assistant.

Analyze the resume text below and extract structured information.

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

Rules:

1. Do not invent information that does not exist in the resume.
2. If information is missing, use null.
3. Keep skills as individual items.
4. Preserve the meaning of experience and project descriptions.
5. Keep dates in the format found in the resume when possible.
6. A project is different from work experience.
7. Education and work experience must not be mixed.
8. Return all relevant skills, experiences, education entries, and projects.
9. The resume may use Indonesian or English.
10. Understand different section names and resume layouts.

Resume text:

---BEGIN RESUME---

{resume_text}

---END RESUME---
"""


def parse_resume_with_ai(
    resume_text: str,
) -> StructuredResume:
    client = GeminiClient()

    prompt = RESUME_PROMPT.format(
        resume_text=resume_text,
    )

    response = client.generate_text(prompt)

    try:
        data = json.loads(response)
    except json.JSONDecodeError as exc:
        raise ValueError("Gemini returned invalid JSON for resume parsing") from exc

    return StructuredResume.model_validate(data)
