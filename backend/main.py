"""PriceHunt API — UAE/MENA price aggregator."""
import asyncio
import os
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from scrapers import dubizzle, amazon_ae, noon, carrefour_ae, sharaf_dg, opensooq

app = FastAPI(title="PriceHunt UAE/MENA API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

SCRAPER_MAP = {
    "amazon": amazon_ae.scrape,
    "noon": noon.scrape,
    "carrefour": carrefour_ae.scrape,
    "sharafdg": sharaf_dg.scrape,
    "dubizzle": dubizzle.scrape,
    "opensooq": opensooq.scrape,
}

LOCATION_SCRAPERS = {"dubizzle", "opensooq"}
ALL_SOURCES = list(SCRAPER_MAP.keys())


@app.get("/api/search")
async def search(
    query: str = Query(..., description="Item to search for"),
    location: Optional[str] = Query("Dubai", description="City/country for local results"),
    sources: Optional[str] = Query("all", description="Comma-separated sources or 'all'"),
):
    source_list = (
        ALL_SOURCES
        if sources == "all"
        else [s.strip().lower() for s in sources.split(",") if s.strip().lower() in SCRAPER_MAP]
    )
    if not source_list:
        source_list = ALL_SOURCES

    coros = []
    for src in source_list:
        fn = SCRAPER_MAP[src]
        if src in LOCATION_SCRAPERS:
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

    # Sort by price (None prices go to end)
    all_results.sort(key=lambda x: (x["price"] is None, x["price"] or 0))

    best = next((r for r in all_results if r["price"] is not None), None)

    return {
        "query": query,
        "location": location,
        "total": len(all_results),
        "best_price": {
            "price": best["price"],
            "price_text": best["price_text"],
            "source": best["source"],
            "url": best["url"],
            "currency": best.get("currency", "AED"),
        } if best else None,
        "results": all_results,
        "errors": errors,
    }


@app.get("/api/sources")
async def list_sources():
    return {
        "sources": [
            {"id": "amazon", "name": "Amazon.ae", "type": "web", "icon": "🛒"},
            {"id": "noon", "name": "Noon", "type": "web", "icon": "🌙"},
            {"id": "carrefour", "name": "Carrefour UAE", "type": "web", "icon": "🏪"},
            {"id": "sharafdg", "name": "Sharaf DG", "type": "web", "icon": "📱"},
            {"id": "dubizzle", "name": "Dubizzle", "type": "local", "icon": "📍"},
            {"id": "opensooq", "name": "OpenSooq", "type": "local", "icon": "🗺️"},
        ]
    }


@app.get("/api/health")
async def health():
    return {"status": "ok", "region": "UAE/MENA"}


# Serve the single-file frontend
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
FRONTEND_INDEX = os.path.join(STATIC_DIR, "index.html")


@app.get("/")
async def serve_index():
    return FileResponse(FRONTEND_INDEX)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
