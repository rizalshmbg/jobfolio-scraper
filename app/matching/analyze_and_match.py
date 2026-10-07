from .final_matcher import FinalMatchResult
from .matcher import match_resume_to_job
from ..job.ai_normalizer import normalize_job_with_ai
from ..job.ai_parser import parse_job_with_ai
from ..job.models import StructuredJob
from ..resume.ai_normalizer import normalize_resume_with_ai
from ..resume.ai_parser import parse_resume_with_ai
from ..resume.extractor import extract_resume_text


def analyze_and_match(
    file_bytes: bytes,
    mime_type: str,
    job_data: dict,
) -> FinalMatchResult:
    # 1. Extract resume text
    resume_text = extract_resume_text(
        file_bytes=file_bytes,
        mime_type=mime_type,
    )

    if not resume_text:
        raise ValueError("Unable to extract text from resume")

    # 2. Parse resume with AI
    parsed_resume = parse_resume_with_ai(resume_text)

    # 3. Normalize resume with AI
    normalized_resume = normalize_resume_with_ai(parsed_resume)

    # 4. Parse job with AI
    parsed_job = parse_job_with_ai(job_data)

    # 5. Normalize job with AI
    normalized_job = normalize_job_with_ai(parsed_job)

    # 6. Match normalized resume against normalized job
    return match_resume_to_job(
        resume=normalized_resume,
        job=normalized_job,
    )
