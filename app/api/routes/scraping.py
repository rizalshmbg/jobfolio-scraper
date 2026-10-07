from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

from ...scraping.fetcher import fetch_job_page
from ...scraping.platforms import scrape_by_platform

router = APIRouter()


class ScrapeRequest(BaseModel):
    url: HttpUrl


@router.post("/scrape")
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
