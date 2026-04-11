"""PriceHunt API — UAE/MENA comprehensive price aggregator."""
import asyncio, os, re
from typing import Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from scrapers import (
    dubizzle, amazon_ae, noon, carrefour_ae, sharaf_dg, opensooq,
    lulu, virgin, jumbo, namshi, aliexpress, desertcart,
)

app = FastAPI(title="PriceHunt UAE/MENA API", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# id → (scraper_fn, needs_location)
SCRAPERS = {
    "amazon":      (amazon_ae.scrape,    False),
    "noon":        (noon.scrape,         False),
    "carrefour":   (carrefour_ae.scrape, False),
    "sharafdg":    (sharaf_dg.scrape,    False),
    "lulu":        (lulu.scrape,         False),
    "virgin":      (virgin.scrape,       False),
    "jumbo":       (jumbo.scrape,        False),
    "namshi":      (namshi.scrape,       False),
    "desertcart":  (desertcart.scrape,   False),
    "dubizzle":    (dubizzle.scrape,     True),
    "opensooq":    (opensooq.scrape,     True),
    "aliexpress":  (aliexpress.scrape,   False),
}

ALL_SOURCES = list(SCRAPERS.keys())

# ── Result validation ─────────────────────────────────────────────────────────
_JUNK_PHRASES = [
    "browse by category", "you searched for", "sign in", "log in", "my account",
    "shopping cart", "wishlist", "free delivery on orders", "download the app",
    "download app", "cookie policy", "privacy policy", "terms and conditions",
    "terms of use", "customer service", "track your order", "become a seller",
    "back to top", "newsletter", "subscribe", "all rights reserved",
    "contact us", "about us", "store locator",
]

def _is_valid_result(r: dict) -> bool:
    """Return False for results that are clearly scraped UI chrome, not products."""
    title = (r.get("title") or "").strip()
    price = r.get("price")

    # Too short to be a product name
    if len(title) < 6:
        return False

    # Looks like a navigation / UI element
    tl = title.lower()
    if any(phrase in tl for phrase in _JUNK_PHRASES):
        return False

    # Sanity-check numeric price (0.5–500,000 AED covers everything realistically)
    if price is not None and (price < 0.5 or price > 500_000):
        return False

    return True


@app.get("/api/search")
async def search(
    query: str = Query(...),
    location: Optional[str] = Query("Dubai"),
    sources: Optional[str] = Query("all"),
):
    source_list = (
        ALL_SOURCES if sources == "all"
        else [s.strip().lower() for s in sources.split(",") if s.strip().lower() in SCRAPERS]
    ) or ALL_SOURCES

    coros = []
    for src in source_list:
        fn, needs_loc = SCRAPERS[src]
        coros.append(fn(query, location) if needs_loc else fn(query))

    results_list = await asyncio.gather(*coros, return_exceptions=True)

    all_results, errors, source_stats = [], [], {}
    for src, result in zip(source_list, results_list):
        if isinstance(result, Exception):
            errors.append({"source": src, "error": str(result)})
            source_stats[src] = 0
        else:
            # Filter garbage before counting
            valid = [r for r in result if _is_valid_result(r)]
            all_results.extend(valid)
            source_stats[src] = len(valid)

    all_results.sort(key=lambda x: (x["price"] is None, x["price"] or 0))
    best = next((r for r in all_results if r["price"] is not None), None)

    return {
        "query": query,
        "location": location,
        "total": len(all_results),
        "source_stats": source_stats,
        "best_price": {
            "price": best["price"],
            "price_text": best["price_text"],
            "source": best["source"],
            "url": best["url"],
        } if best else None,
        "results": all_results,
        "errors": errors,
    }


@app.get("/api/sources")
async def list_sources():
    return {"sources": [
        {"id": "amazon",     "name": "Amazon.ae",        "type": "web",   "icon": "🛒"},
        {"id": "noon",       "name": "Noon",              "type": "web",   "icon": "🌙"},
        {"id": "carrefour",  "name": "Carrefour UAE",     "type": "web",   "icon": "🏪"},
        {"id": "sharafdg",   "name": "Sharaf DG",         "type": "web",   "icon": "📱"},
        {"id": "lulu",       "name": "Lulu Hypermarket",  "type": "web",   "icon": "🛍️"},
        {"id": "virgin",     "name": "Virgin Megastore",  "type": "web",   "icon": "🎵"},
        {"id": "jumbo",      "name": "Jumbo Electronics", "type": "web",   "icon": "⚡"},
        {"id": "namshi",     "name": "Namshi",            "type": "web",   "icon": "👗"},
        {"id": "desertcart", "name": "Desertcart",        "type": "web",   "icon": "🌐"},
        {"id": "dubizzle",   "name": "Dubizzle",          "type": "local", "icon": "📍"},
        {"id": "opensooq",   "name": "OpenSooq",          "type": "local", "icon": "🗺️"},
        {"id": "aliexpress", "name": "AliExpress",        "type": "web",   "icon": "🌏"},
    ]}


@app.get("/api/health")
async def health():
    return {"status": "ok", "region": "UAE/MENA", "sources": len(SCRAPERS)}


# Serve single-file frontend
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
