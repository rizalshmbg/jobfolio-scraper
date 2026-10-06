from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

from .fetcher import fetch_job_page
from .scrapers import scrape_by_platform

from .config import settings

from .job.models import StructuredJob
from .matching.api_models import MatchRequest, MatchResponse
from .matching.matcher import match_resume_to_job
from .resume.normalized_models import NormalizedResume

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
