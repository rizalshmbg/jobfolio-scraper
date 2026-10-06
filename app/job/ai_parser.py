import json

from ..ai.client import GeminiClient
from .models import StructuredJob

JOB_PROMPT = """
You are a job description parsing assistant.

Analyze the job information below and extract structured information.

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

Rules:

1. Do not invent information that does not exist in the job information.
2. If information is missing, use null for scalar fields and [] for lists.
3. Preserve the original meaning of the job information.
4. Keep skills as individual items.
5. Put specific technologies, programming languages, frameworks, libraries, tools, platforms, databases, and technical skills explicitly required by the employer into requiredSkills.
6. Put specific technologies, programming languages, frameworks, libraries, tools, platforms, databases, and technical skills explicitly described as preferred, nice-to-have, bonus, or plus into preferredSkills.
7. Do not put the same skill into both requiredSkills and preferredSkills.
8. Do not put skill names into qualifications when the same skill is already represented in requiredSkills or preferredSkills.
9. For example:
   - "Experience with React.js" -> requiredSkills: ["React.js"]
   - Do NOT also put "Experience with React.js" into qualifications.
10. Put non-skill candidate requirements into qualifications.
11. Examples of qualifications include:
   - education requirements
   - years of experience
   - language requirements
   - certifications
   - soft-skill requirements
   - domain knowledge
   - general knowledge requirements
12. Put duties and tasks into responsibilities.
13. Do not treat every qualification as a skill.
14. Do not duplicate the same information unnecessarily.
15. Understand both Indonesian and English job descriptions.
16. Keep the job title, company, location, employment type, and work arrangement when available.
17. Do not infer a skill merely because it is implied by another skill.
18. Do not invent years of experience, education requirements, or technologies.
19. Keep the original job description available in the description field when provided.
20. If a qualification contains both a skill and additional non-skill information, extract the skill into the appropriate skill list and keep only the remaining meaningful qualification information in qualifications.

Job information:

---BEGIN JOB INFORMATION---

{job_json}

---END JOB INFORMATION---
"""


def parse_job_with_ai(
    job: dict,
) -> StructuredJob:
    client = GeminiClient()

    job_json = json.dumps(
        job,
        ensure_ascii=False,
        indent=2,
    )

    prompt = JOB_PROMPT.format(
        job_json=job_json,
    )

    response = client.generate_text(prompt)

    try:
        data = json.loads(response)
    except json.JSONDecodeError as exc:
        raise ValueError("Gemini returned invalid JSON for job parsing") from exc

    return StructuredJob.model_validate(data)
