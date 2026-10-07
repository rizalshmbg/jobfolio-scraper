from fastapi import FastAPI

from .api.routes.health import router as health_router
from .api.routes.scraping import router as scraping_router
from .api.routes.matching import router as matching_router

app = FastAPI(
    title="JobFolio Scraper",
    version="1.0.0",
)


app.include_router(health_router)
app.include_router(scraping_router)
app.include_router(matching_router)
