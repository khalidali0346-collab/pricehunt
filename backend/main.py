"""PriceHunt UAE/MENA — Universal price aggregator v5."""
import asyncio, os
from typing import Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from scrapers import (
    # Online + Physical stores
    amazon_ae, noon, carrefour_ae, sharaf_dg, lulu, virgin, jumbo, emax,
    # Online only
    namshi, desertcart, sixthstreet, mumzworld, ounass,
    # Furniture / Home
    ikea_ae,
    # Sports
    sun_sand,
    # Cars
    yallamotor,
    # Classifieds (local)
    dubizzle, opensooq,
    # Social
    instagram_uae,
)

app = FastAPI(title="PriceHunt UAE/MENA", version="5.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# (fn, needs_location, category)
SCRAPERS = {
    "amazon":      (amazon_ae.scrape,     False, "general"),
    "noon":        (noon.scrape,          False, "general"),
    "carrefour":   (carrefour_ae.scrape,  False, "general"),
    "sharafdg":    (sharaf_dg.scrape,     False, "electronics"),
    "lulu":        (lulu.scrape,          False, "general"),
    "virgin":      (virgin.scrape,        False, "electronics"),
    "jumbo":       (jumbo.scrape,         False, "electronics"),
    "emax":        (emax.scrape,          False, "electronics"),
    "namshi":      (namshi.scrape,        False, "fashion"),
    "sixthstreet": (sixthstreet.scrape,   False, "fashion"),
    "ounass":      (ounass.scrape,        False, "fashion"),
    "desertcart":  (desertcart.scrape,    False, "general"),
    "ikea":        (ikea_ae.scrape,       False, "home"),
    "sunsand":     (sun_sand.scrape,      False, "sports"),
    "mumzworld":   (mumzworld.scrape,     False, "baby"),
    "yallamotor":  (yallamotor.scrape,    False, "cars"),
    "dubizzle":    (dubizzle.scrape,      True,  "classifieds"),
    "opensooq":    (opensooq.scrape,      True,  "classifieds"),
    "instagram":   (instagram_uae.scrape, False, "social"),
}

ALL = list(SCRAPERS.keys())

SOURCE_META = [
    {"id":"amazon",      "name":"Amazon.ae",        "type":"web",       "store_type":"both",     "icon":"🛒", "category":"general"},
    {"id":"noon",        "name":"Noon",              "type":"web",       "store_type":"online",   "icon":"🌙", "category":"general"},
    {"id":"carrefour",   "name":"Carrefour UAE",     "type":"web",       "store_type":"both",     "icon":"🏪", "category":"general"},
    {"id":"sharafdg",    "name":"Sharaf DG",         "type":"web",       "store_type":"both",     "icon":"📱", "category":"electronics"},
    {"id":"lulu",        "name":"Lulu Hypermarket",  "type":"web",       "store_type":"both",     "icon":"🛍️", "category":"general"},
    {"id":"virgin",      "name":"Virgin Megastore",  "type":"web",       "store_type":"both",     "icon":"🎵", "category":"electronics"},
    {"id":"jumbo",       "name":"Jumbo Electronics", "type":"web",       "store_type":"both",     "icon":"⚡", "category":"electronics"},
    {"id":"emax",        "name":"Emax",              "type":"web",       "store_type":"both",     "icon":"🖥️", "category":"electronics"},
    {"id":"namshi",      "name":"Namshi",            "type":"web",       "store_type":"online",   "icon":"👗", "category":"fashion"},
    {"id":"sixthstreet", "name":"6th Street",        "type":"web",       "store_type":"online",   "icon":"👠", "category":"fashion"},
    {"id":"ounass",      "name":"Ounass",            "type":"web",       "store_type":"online",   "icon":"💎", "category":"fashion"},
    {"id":"desertcart",  "name":"Desertcart",        "type":"web",       "store_type":"online",   "icon":"🌐", "category":"general"},
    {"id":"ikea",        "name":"IKEA UAE",          "type":"web",       "store_type":"both",     "icon":"🛋️", "category":"home"},
    {"id":"sunsand",     "name":"Sun & Sand Sports", "type":"web",       "store_type":"both",     "icon":"⚽", "category":"sports"},
    {"id":"mumzworld",   "name":"Mumzworld",         "type":"web",       "store_type":"online",   "icon":"🍼", "category":"baby"},
    {"id":"yallamotor",  "name":"YallaMotor",        "type":"web",       "store_type":"both",     "icon":"🚗", "category":"cars"},
    {"id":"dubizzle",    "name":"Dubizzle",          "type":"local",     "store_type":"physical", "icon":"📍", "category":"classifieds"},
    {"id":"opensooq",    "name":"OpenSooq",          "type":"local",     "store_type":"physical", "icon":"🗺️", "category":"classifieds"},
    {"id":"instagram",   "name":"Instagram",         "type":"instagram", "store_type":"both",     "icon":"📸", "category":"social"},
]


@app.get("/api/search")
async def search(
    query: str = Query(...),
    location: Optional[str] = Query("Dubai"),
    sources: Optional[str] = Query("all"),
    category: Optional[str] = Query("all"),
):
    src_list = (
        ALL if sources == "all"
        else [s.strip().lower() for s in sources.split(",") if s.strip().lower() in SCRAPERS]
    ) or ALL

    # Filter by category if specified
    if category and category != "all":
        src_list = [s for s in src_list if SCRAPERS[s][2] == category or SCRAPERS[s][2] == "general"]

    coros = []
    for s in src_list:
        fn, needs_loc, _ = SCRAPERS[s]
        coros.append(fn(query, location) if needs_loc else fn(query))

    raw = await asyncio.gather(*coros, return_exceptions=True)

    all_results, errors, stats = [], [], {}
    for s, res in zip(src_list, raw):
        if isinstance(res, Exception):
            errors.append({"source": s, "error": str(res)})
            stats[s] = 0
        else:
            all_results.extend(res)
            stats[s] = len(res)

    all_results.sort(key=lambda x: (x["price"] is None, x["price"] or 0))
    best = next((r for r in all_results if r["price"] is not None), None)

    return {
        "query": query,
        "location": location,
        "total": len(all_results),
        "source_stats": stats,
        "best_price": {
            "price": best["price"],
            "price_text": best["price_text"],
            "source": best["source"],
            "url": best["url"],
            "store_type": best.get("store_type", "online"),
        } if best else None,
        "results": all_results,
        "errors": errors,
    }


@app.get("/api/sources")
async def get_sources():
    return {"sources": SOURCE_META}


@app.get("/api/health")
async def health():
    return {"status": "ok", "sources": len(SCRAPERS), "region": "UAE/MENA"}


STATIC = os.path.join(os.path.dirname(__file__), "static")

@app.get("/")
async def index():
    return FileResponse(os.path.join(STATIC, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
