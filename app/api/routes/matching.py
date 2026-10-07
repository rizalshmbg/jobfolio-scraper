import json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import ValidationError

from ...matching.analyze_and_match import analyze_and_match
from ...matching.api_models import AnalyzeAndMatchJob, AnalyzeAndMatchResponse

router = APIRouter()


MAX_RESUME_FILE_SIZE = 5 * 1024 * 1024

ALLOWED_RESUME_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.post(
    "/analyze-and-match",
    response_model=AnalyzeAndMatchResponse,
)
async def analyze_and_match_endpoint(
    resume: UploadFile = File(...),
    job: str = Form(...),
):
    try:
        if resume.content_type not in ALLOWED_RESUME_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail="Resume file must be PDF, DOC, or DOCX",
            )

        file_bytes = await resume.read()

        if not file_bytes:
            raise HTTPException(
                status_code=400,
                detail="Resume file is empty",
            )

        if len(file_bytes) > MAX_RESUME_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail="Resume file size must not exceed 5 MB",
            )

        try:
            job_json = json.loads(job)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid job JSON",
            ) from exc

        try:
            job_data = AnalyzeAndMatchJob.model_validate(job_json)
        except ValidationError as exc:
            raise HTTPException(
                status_code=422,
                detail="Invalid job data",
            ) from exc

        result = analyze_and_match(
            file_bytes=file_bytes,
            mime_type=resume.content_type,
            job_data=job_data.model_dump(),
        )

        return {
            "success": True,
            "message": "Resume analyzed and matched successfully",
            "data": result.__dict__,
        }

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to analyze and match resume",
        ) from exc
