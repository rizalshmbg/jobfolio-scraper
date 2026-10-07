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

Rules:

1. Do not invent information that does not exist in the job information.

2. If information is missing:
   - use null for scalar fields
   - use [] for list fields

3. Preserve the original meaning of the job information.

4. Extract specific technologies, programming languages, frameworks,
   libraries, APIs, tools, platforms, databases, and other technical
   skills explicitly mentioned by the employer.

5. Use requiredSkills only for technical skills that are explicitly
   required, expected, or stated as necessary by the employer.

6. Use preferredSkills for technical skills explicitly described as:
   - preferred
   - nice to have
   - bonus
   - plus
   - nilai tambah
   - diutamakan
   - menjadi nilai tambah

7. Do not put the same skill into both requiredSkills and preferredSkills.

8. Each item in requiredSkills and preferredSkills must be a
   SkillRequirement object with:
   - "skills": a list of related alternative skills
   - "operator": either "AND" or "OR"

9. Use operator "OR" when the job explicitly presents alternatives,
   such as:
   - "A or B"
   - "A atau B"
   - "A / B"
   - "A atau B"
   - "A dan/atau B"
   - "A/B"
   - "A, B, or C"

10. When using operator "OR", put the alternative skills into the
    same SkillRequirement object.

    Example:
    "JavaScript dan/atau TypeScript"

    should become:

    {{
      "skills": ["JavaScript", "TypeScript"],
      "operator": "OR"
    }}

11. Another example:

    "React.js atau Next.js"

    should become:

    {{
      "skills": ["React.js", "Next.js"],
      "operator": "OR"
    }}

12. Another example:

    "PostgreSQL atau MySQL"

    should become:

    {{
      "skills": ["PostgreSQL", "MySQL"],
      "operator": "OR"
    }}

13. Use operator "AND" when multiple skills are independently required
    and the candidate is expected to have all of them.

    Example:

    "Menguasai Python dan REST API"

    should become two independent requirements:

    {{
      "skills": ["Python"],
      "operator": "AND"
    }},
    {{
      "skills": ["REST API"],
      "operator": "AND"
    }}

14. Do not use OR merely because multiple technologies are mentioned
    in the same sentence. Only use OR when the wording indicates
    alternatives.

15. Do not split a primary technology from its related platform or
    ecosystem into independent requirements when the job treats them
    as one capability.

    Example:

    "Git (GitHub/GitLab)"

    should NOT become:

    - Git
    - GitHub
    - GitLab

    Instead, represent the primary technical skill as:

    {{
      "skills": ["Git"],
      "operator": "AND"
    }}

16. Treat GitHub and GitLab as related platforms/tools when they are
    only mentioned as examples or platforms for using Git.

17. Do not infer a skill merely because it is implied by another skill.

18. Preserve specific technology distinctions.

    Do not merge:
    - Java with JavaScript
    - React with React Native
    - Next.js with React
    - Django with Django REST Framework
    - PostgreSQL with MySQL
    - Git with GitHub or GitLab

19. If a framework and its extension/API are explicitly presented as
    alternatives, they may belong to the same OR group.

    Example:

    "Django / Django REST Framework"

    should become:

    {{
      "skills": ["Django", "Django REST Framework"],
      "operator": "OR"
    }}

20. If one technology is required and another is only a preferred
    extension or bonus, keep them in separate requiredSkills and
    preferredSkills groups.

21. Do not put skill names into qualifications when the same skill is
    already represented in requiredSkills or preferredSkills.

22. For example:

    "Experience with React.js"

    should become:

    {{
      "skills": ["React.js"],
      "operator": "AND"
    }}

    Do NOT also put React.js into qualifications.

23. Put non-skill candidate requirements into qualifications.

24. Examples of qualifications include:
    - education requirements
    - years of experience
    - language requirements
    - certifications
    - soft-skill requirements
    - domain knowledge
    - general knowledge requirements

25. Put duties and tasks into responsibilities.

26. Do not treat every qualification as a technical skill.

27. Do not duplicate the same information unnecessarily.

28. Understand both Indonesian and English job descriptions.

29. Keep the job title, company, location, employment type, and
    work arrangement when available.

30. Do not invent years of experience, education requirements,
    technologies, responsibilities, or qualifications.

31. Keep the original job description available in the description
    field when provided.

32. If a qualification contains both a skill and additional
    non-skill information, extract the skill into the appropriate
    skill list and keep only the remaining meaningful qualification
    information in qualifications.

33. Prefer semantic grouping over blindly splitting every technology
    name into a separate requirement.

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
