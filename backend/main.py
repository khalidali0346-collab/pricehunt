"""PriceHunt API — aggregates prices from multiple sources."""
import asyncio
import os
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from scrapers import ebay, craigslist, google_shopping, instagram, walmart

app = FastAPI(title="PriceHunt API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

SCRAPER_MAP = {
    "ebay": ebay.scrape,
    "craigslist": craigslist.scrape,
    "google": google_shopping.scrape,
    "instagram": instagram.scrape,
    "walmart": walmart.scrape,
}

ALL_SOURCES = list(SCRAPER_MAP.keys())


@app.get("/api/search")
async def search(
    query: str = Query(..., description="Item to search for"),
    location: Optional[str] = Query(None, description="City for local (Craigslist) results"),
    sources: Optional[str] = Query("all", description="Comma-separated sources or 'all'"),
):
    source_list = (
        ALL_SOURCES
        if sources == "all"
        else [s.strip().lower() for s in sources.split(",") if s.strip().lower() in SCRAPER_MAP]
    )
    if not source_list:
        source_list = ALL_SOURCES

    # Build coroutines — craigslist needs location param
    coros = []
    for src in source_list:
        fn = SCRAPER_MAP[src]
        if src == "craigslist":
            coros.append(fn(query, location))
        else:
            coros.append(fn(query))

    results_list = await asyncio.gather(*coros, return_exceptions=True)

    all_results = []
    errors = []
    for src, result in zip(source_list, results_list):
        if isinstance(result, Exception):
            errors.append({"source": src, "error": str(result)})
        else:
            all_results.extend(result)

    # Sort by price (None prices go to the end)
    all_results.sort(key=lambda x: (x["price"] is None, x["price"] or 0))

    best = all_results[0] if all_results else None

    return {
        "query": query,
        "location": location,
        "total": len(all_results),
        "best_price": {
            "price": best["price"],
            "price_text": best["price_text"],
            "source": best["source"],
            "url": best["url"],
        } if best and best["price"] is not None else None,
        "results": all_results,
        "errors": errors,
    }


@app.get("/api/sources")
async def list_sources():
    return {
        "sources": [
            {"id": "ebay", "name": "eBay", "type": "web", "icon": "🛒"},
            {"id": "walmart", "name": "Walmart", "type": "web", "icon": "🏪"},
            {"id": "google", "name": "Google Shopping", "type": "web", "icon": "🔍"},
            {"id": "craigslist", "name": "Craigslist", "type": "local", "icon": "📍"},
            {"id": "instagram", "name": "Instagram", "type": "instagram", "icon": "📸"},
        ]
    }


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Serve React build if it exists
FRONTEND_BUILD = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(FRONTEND_BUILD):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_BUILD, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        index = os.path.join(FRONTEND_BUILD, "index.html")
        return FileResponse(index)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
