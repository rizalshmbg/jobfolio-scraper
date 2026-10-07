from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, HttpUrl, ValidationError

from .fetcher import fetch_job_page
from .scrapers import scrape_by_platform

from .config import settings

from .job.models import StructuredJob
from .matching.api_models import MatchRequest, MatchResponse
from .matching.matcher import match_resume_to_job
from .resume.normalized_models import NormalizedResume

import json

from .matching.analyze_and_match import analyze_and_match
from .matching.api_models import AnalyzeAndMatchResponse, AnalyzeAndMatchJob

MAX_RESUME_FILE_SIZE = 5 * 1024 * 1024

ALLOWED_RESUME_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

app = FastAPI(
    title="JobFolio Scraper",
    version="1.0.0",
)


class ScrapeRequest(BaseModel):
    url: HttpUrl


@app.get("/health")
async def health():
    return {
        "success": True,
        "service": "jobfolio-scraper",
    }


@app.post("/scrape")
async def scrape_job(data: ScrapeRequest):
    url = str(data.url)

    try:
        html = await fetch_job_page(url)

        result = scrape_by_platform(
            html,
            url,
        )

        return {
            "success": True,
            "message": "Job information imported successfully",
            "data": result,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    except TimeoutError as exc:
        raise HTTPException(
            status_code=408,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to scrape job page",
        ) from exc


@app.post("/match", response_model=MatchResponse)
async def match_resume(data: MatchRequest):
    try:
        resume = NormalizedResume.model_validate(data.resume)
        job = StructuredJob.model_validate(data.job)

        result = match_resume_to_job(
            resume=resume,
            job=job,
        )

        return {
            "success": True,
            "message": "Resume matched successfully",
            "data": result.__dict__,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to match resume to job",
        ) from exc


@app.post(
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
