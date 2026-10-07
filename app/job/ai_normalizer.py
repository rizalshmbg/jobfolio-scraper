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
  "requiredSkills": [
    {{
      "skills": [],
      "operator": "AND"
    }}
  ],
  "preferredSkills": [
    {{
      "skills": [],
      "operator": "AND"
    }}
  ],
  "responsibilities": [],
  "qualifications": []
}}

Normalization rules:

1. Do not invent information.

2. Do not remove meaningful information.

3. Normalize every skill name into a consistent canonical form.

4. Preserve the structure of every SkillRequirement.

5. NEVER remove, change, or reinterpret the operator.

6. The operator must remain exactly either:
   - "AND"
   - "OR"

7. Preserve the difference between alternative skills and independently
   required skills.

8. Examples of normalization:

   - React.js, ReactJS, React JS -> react
   - Next.js, NextJS, Next JS -> next.js
   - Node.js, NodeJS, Node JS -> nodejs
   - REST API, REST APIs, RESTful API, RESTful APIs -> rest api
   - TypeScript, Typescript -> typescript
   - JavaScript, Javascript -> javascript
   - PostgreSQL, Postgres -> postgresql
   - MySQL, MySql -> mysql
   - GitHub, Github -> github
   - GitLab, Gitlab -> gitlab
   - Python, python -> python
   - Django, django -> django

9. Example:

   Input:

   {{
     "skills": ["React.js", "Next.js"],
     "operator": "OR"
   }}

   Output:

   {{
     "skills": ["react", "next.js"],
     "operator": "OR"
   }}

10. Another example:

   Input:

   {{
     "skills": ["PostgreSQL", "MySQL"],
     "operator": "OR"
   }}

   Output:

   {{
     "skills": ["postgresql", "mysql"],
     "operator": "OR"
   }}

11. Another example:

   Input:

   {{
     "skills": ["Git"],
     "operator": "AND"
   }}

   Output:

   {{
     "skills": ["git"],
     "operator": "AND"
   }}

12. Do NOT merge different technologies just because they are related.

13. For example:
   - Java is NOT JavaScript.
   - React is NOT React Native.
   - React is NOT Next.js.
   - Vue is NOT Vue Native.
   - Angular is NOT AngularJS.
   - PostgreSQL is NOT MySQL.
   - Git is NOT GitHub.
   - GitHub is NOT GitLab.
   - Django is NOT Django REST Framework.

14. Do not change the logical relationship between skills.

15. Do not convert an OR group into an AND group.

16. Do not convert an AND group into an OR group.

17. Do not move a skill between requiredSkills and preferredSkills.

18. Keep requiredSkills and preferredSkills separate.

19. Do not invent skills from responsibilities or qualifications.

20. Keep responsibilities separate from skills.

21. Keep qualifications separate from skills.

22. Do not rewrite responsibilities unnecessarily.

23. Do not rewrite qualifications unnecessarily.

24. Keep company name, title, location, employment type, and
    work arrangement unchanged unless there is an obvious formatting
    variation.

25. The purpose of normalization is to make later job matching more
    consistent, not to change the meaning of the job.

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
