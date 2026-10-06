import json

from ..ai.client import GeminiClient
from .models import StructuredJob

JOB_NORMALIZER_PROMPT = """
You are a job description normalization assistant.

Normalize the structured job below for later semantic job matching.

Return ONLY valid JSON.
Do not use Markdown.
Do not add explanations.

Use exactly this JSON structure:

{{
  "title": null,
  "company": null,
  "description": null,
  "location": null,
  "employmentType": null,
  "workArrangement": null,
  "requiredSkills": [],
  "preferredSkills": [],
  "responsibilities": [],
  "qualifications": []
}}

Normalization rules:

1. Do not invent information.
2. Do not remove meaningful information.
3. Normalize skill names into consistent canonical forms.
4. Treat obvious spelling and naming variations as the same skill.
5. Examples:
   - React.js, ReactJS, React JS -> react
   - Node.js, NodeJS, Node JS -> nodejs
   - REST API, REST APIs, RESTful API, RESTful APIs -> rest api
   - TypeScript, Typescript -> typescript
   - JavaScript, Javascript -> javascript
6. Do NOT merge different technologies just because they are related.
7. For example:
   - Java is NOT JavaScript.
   - React is NOT React Native.
   - Vue is NOT Vue Native.
   - Angular is NOT AngularJS.
8. Keep requiredSkills and preferredSkills separate.
9. Do not move a required skill into preferredSkills.
10. Do not move a preferred skill into requiredSkills.
11. Keep responsibilities separate from skills.
12. Keep qualifications separate from skills.
13. Do not invent skills from responsibilities or qualifications.
14. Preserve the original meaning of responsibilities.
15. Preserve the original meaning of qualifications.
16. Keep company name, title, dates, location, employment type, and work arrangement unchanged unless there is an obvious formatting variation.
17. The purpose of normalization is to make later job matching more consistent, not to rewrite the job description.

Structured job:

---BEGIN STRUCTURED JOB---

{job_json}

---END STRUCTURED JOB---
"""


def normalize_job_with_ai(
    job: StructuredJob,
) -> StructuredJob:
    client = GeminiClient()

    job_json = job.model_dump_json()

    prompt = JOB_NORMALIZER_PROMPT.format(
        job_json=job_json,
    )

    response = client.generate_text(prompt)

    try:
        data = json.loads(response)
    except json.JSONDecodeError as exc:
        raise ValueError("Gemini returned invalid JSON for job normalization") from exc

    return StructuredJob.model_validate(data)
