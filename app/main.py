from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

from .fetcher import fetch_job_page
from .scrapers import scrape_by_platform

from .config import settings


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