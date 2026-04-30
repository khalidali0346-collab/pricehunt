"""PriceHunt API — UAE/MENA comprehensive price aggregator."""
import asyncio, os, re
from typing import Optional
from urllib.parse import quote_plus
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from scrapers import (
    dubizzle, amazon_ae, noon, carrefour_ae, sharaf_dg, opensooq,
    lulu, virgin, jumbo, namshi, aliexpress, desertcart, ebay, google_shopping, emax,
    microless,
)

app = FastAPI(title="PriceHunt UAE/MENA API", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# id → (scraper_fn, needs_location)
SCRAPERS = {
    "amazon":      (amazon_ae.scrape,       False),
    "noon":        (noon.scrape,            False),
    "carrefour":   (carrefour_ae.scrape,    False),
    "sharafdg":    (sharaf_dg.scrape,       False),
    "lulu":        (lulu.scrape,            False),
    "virgin":      (virgin.scrape,          False),
    "jumbo":       (jumbo.scrape,           False),
    "namshi":      (namshi.scrape,          False),
    "desertcart":  (desertcart.scrape,      False),
    "dubizzle":    (dubizzle.scrape,        True),
    "opensooq":    (opensooq.scrape,        True),
    "aliexpress":  (aliexpress.scrape,      False),
    "ebay":        (ebay.scrape,            False),
    "google":      (google_shopping.scrape, False),
    "emax":        (emax.scrape,            False),
    "microless":   (microless.scrape,       False),
}

ALL_SOURCES = list(SCRAPERS.keys())

# ── Junk filter ───────────────────────────────────────────────────────────────
_JUNK_PHRASES = [
    "browse by category", "you searched for", "sign in", "log in", "my account",
    "shopping cart", "wishlist", "free delivery on orders", "download the app",
    "download app", "cookie policy", "privacy policy", "terms and conditions",
    "terms of use", "customer service", "track your order", "become a seller",
    "back to top", "newsletter", "subscribe", "all rights reserved",
    "contact us", "about us", "store locator",
]

def _is_valid_result(r: dict) -> bool:
    title = (r.get("title") or "").strip()
    price = r.get("price")
    if len(title) < 6:
        return False
    tl = title.lower()
    if any(phrase in tl for phrase in _JUNK_PHRASES):
        return False
    if price is not None and (price < 0.5 or price > 500_000):
        return False
    return True


# ── Relevance scoring ─────────────────────────────────────────────────────────
# Words that indicate the result is an accessory, not the main product
_ACCESSORY_TERMS = [
    "case", "cover", "screen protector", "tempered glass", "glass protector",
    "holder", "charger", "cable", "adapter", "stand", "pouch", "wallet",
    "bumper", "skin", "sticker", "lens protector", "privacy screen",
    "flip cover", "back cover", "silicone case", "clear case", "protective case",
    "armband", "car mount", "pop socket", "popsocket", "ring holder",
    "strap", "band", "dock", "hub", "lightning cable", "usb-c cable",
    "screen guard", "privacy film", "folio", "sleeve", "bag",
    "compatible with", "for iphone", "for samsung", "for apple",
    "2 pack", "3 pack", "4 pack",
]

# Devices / main product categories — searching these means you want the device
_DEVICE_TERMS = [
    "iphone", "samsung galaxy", "galaxy s", "galaxy a", "pixel",
    "oneplus", "xiaomi", "redmi", "oppo", "vivo", "huawei",
    "macbook", "laptop", "notebook", "ipad", "tablet",
    "airpods", "earbuds", "headphones",
    "apple watch", "smartwatch", "smart watch",
    "playstation", "ps5", "ps4", "xbox", "nintendo switch",
    "smart tv", "oled tv", "qled", "4k tv",
    "dslr", "mirrorless camera", "canon", "nikon", "sony camera",
    "electric scooter", "e-bike",
]


def _relevance_score(title: str, query: str) -> int:
    """
    Returns a score (higher = more relevant).
    Penalises accessories when the query is clearly for a device.
    """
    t = title.lower()
    q = query.lower().strip()

    score = 0

    # Title starts with the query → very strong match
    if t.startswith(q):
        score += 100
    elif q in t[:60]:
        score += 60
    elif q in t:
        score += 30

    # All query words appear in title
    words = [w for w in q.split() if len(w) > 2]
    if words and all(w in t for w in words):
        score += 20

    # Query is for a device → penalise accessory results
    q_is_device = any(d in q for d in _DEVICE_TERMS)
    t_is_accessory = any(a in t for a in _ACCESSORY_TERMS)

    if q_is_device and t_is_accessory:
        score -= 80   # Push accessories to the bottom

    return score


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
            valid = [r for r in result if _is_valid_result(r)]
            all_results.extend(valid)
            source_stats[src] = len(valid)

    # Attach relevance score to each result
    for r in all_results:
        r["_relevance"] = _relevance_score(r.get("title", ""), query)

    # Sort: highest relevance first, then cheapest within same relevance band
    all_results.sort(key=lambda x: (
        -x["_relevance"],
        x["price"] is None,
        x["price"] or 0,
    ))

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


@app.get("/api/compare")
async def compare(
    query: str = Query(...),
    location: Optional[str] = Query("Dubai"),
):
    """
    Returns price comparison in clean JSON format — retailer, price, condition,
    URL, in_stock, shipping — sorted by price low to high.
    Used-condition listings (Dubizzle, OpenSooq) are labelled separately.
    """
    source_list = ALL_SOURCES

    coros = []
    for src in source_list:
        fn, needs_loc = SCRAPERS[src]
        coros.append(fn(query, location) if needs_loc else fn(query))

    results_list = await asyncio.gather(*coros, return_exceptions=True)

    all_results = []
    for src, result in zip(source_list, results_list):
        if isinstance(result, Exception):
            continue
        for r in result:
            if not _is_valid_result(r):
                continue
            r["_relevance"] = _relevance_score(r.get("title", ""), query)
            all_results.append(r)

    # Sort: relevance first, then price
    all_results.sort(key=lambda x: (-x["_relevance"], x["price"] is None, x["price"] or 0))

    output = []
    for r in all_results:
        source_type = r.get("source_type", "web")
        condition = r.get("condition", "New")
        if source_type == "local" or "used" in condition.lower():
            condition_label = "used"
        elif "open" in condition.lower():
            condition_label = "open box"
        else:
            condition_label = "new"

        output.append({
            "retailer": r.get("source", ""),
            "price": r.get("price"),
            "price_text": r.get("price_text", ""),
            "condition": condition_label,
            "url": r.get("url", ""),
            "in_stock": r.get("in_stock", True),
            "shipping": r.get("shipping") or "Contact seller",
            "title": r.get("title", ""),
            "image": r.get("image", ""),
        })

    return output


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
        {"id": "ebay",       "name": "eBay",              "type": "web",   "icon": "🛍️"},
        {"id": "google",     "name": "Google Shopping",   "type": "web",   "icon": "🔍"},
        {"id": "emax",       "name": "Emax",              "type": "web",   "icon": "💡"},
        {"id": "microless",  "name": "Microless UAE",     "type": "web",   "icon": "🔧"},
    ]}


@app.get("/api/health")
async def health():
    return {"status": "ok", "region": "UAE/MENA", "sources": len(SCRAPERS)}


@app.get("/api/debug")
async def debug(query: str = Query("iphone 15"), location: str = Query("Dubai")):
    """Run all scrapers and return per-source diagnostics."""
    import traceback
    from scrapers.browser import fetch_rendered, PLAYWRIGHT_AVAILABLE

    diagnostics = {"playwright_available": PLAYWRIGHT_AVAILABLE, "sources": {}}

    async def run_one(src):
        fn, needs_loc = SCRAPERS[src]
        try:
            results = await (fn(query, location) if needs_loc else fn(query))
            valid = [r for r in results if _is_valid_result(r)]
            sample = valid[:2] if valid else results[:2]
            return {
                "status": "ok",
                "total_raw": len(results),
                "total_valid": len(valid),
                "sample": sample,
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc()[-500:],
            }

    tasks = {src: run_one(src) for src in ALL_SOURCES}
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    for src, res in zip(tasks.keys(), results):
        diagnostics["sources"][src] = res if not isinstance(res, Exception) else {
            "status": "exception", "error": str(res)
        }

    return diagnostics


@app.get("/api/debug/raw")
async def debug_raw(query: str = Query("iphone 15")):
    """Raw HTTP probe — checks HTTP status + HTML snippet for each search URL without running full scrapers."""
    import httpx
    from scrapers.utils import get_headers
    from scrapers.browser import PLAYWRIGHT_AVAILABLE

    q = quote_plus(query)
    TEST_URLS = {
        "amazon":    f"https://www.amazon.ae/s?k={q}&s=price-asc-rank",
        "ebay":      f"https://www.ebay.com/sch/i.html?_nkw={q}&_sop=15&LH_BIN=1",
        "google":    f"https://www.google.com/search?q={q}&tbm=shop&hl=en&gl=ae",
        "jumbo":     f"https://www.jumbo.ae/catalogsearch/result/?q={q}",
        "sharafdg":  f"https://www.sharafdg.com/search/?q={q}",
        "emax":      f"https://www.emax.ae/catalogsearch/result/?q={q}",
        "desertcart":f"https://www.desertcart.ae/search?q={q}",
        "noon":      f"https://www.noon.com/uae-en/search/?q={q}",
        "namshi":    f"https://en-ae.namshi.com/search/?q={q}",
    }

    PRODUCT_SIGNALS = [
        "product-item", "s-item__title", "data-asin", "productContainer",
        "product-card", "search-result", "product-name", "item-title",
        "add-to-cart", "addtocart", "__NEXT_DATA__", "application/ld+json",
    ]

    results = {"playwright_available": PLAYWRIGHT_AVAILABLE, "probes": {}}
    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        for name, url in TEST_URLS.items():
            try:
                r = await client.get(url, headers=get_headers(url))
                html = r.text
                found_signals = [s for s in PRODUCT_SIGNALS if s in html]
                results["probes"][name] = {
                    "status": r.status_code,
                    "html_size": len(html),
                    "product_signals": found_signals,
                    "has_products": len(found_signals) > 0,
                    "final_url": str(r.url),
                    "html_preview": html[:400].replace("\n", " ").strip(),
                }
            except Exception as e:
                results["probes"][name] = {"status": "error", "error": str(e)}

    return results


@app.get("/api/playwright-test")
async def playwright_test():
    """Check whether Playwright + Chromium are actually working."""
    from scrapers.browser import test_playwright, PLAYWRIGHT_AVAILABLE
    result = await test_playwright()
    result["playwright_installed"] = PLAYWRIGHT_AVAILABLE
    return result


@app.get("/api/autocomplete")
async def autocomplete(q: str = Query(...)):
    """Return Google search suggestions for the query."""
    import httpx
    if len(q) < 2:
        return []
    url = f"https://suggestqueries.google.com/complete/search?client=firefox&q={quote_plus(q)}&hl=en"
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=5) as client:
            r = await client.get(url, headers={"Accept-Language": "en-AE,en;q=0.9"})
            if r.status_code == 200:
                data = r.json()
                return data[1][:8] if isinstance(data, list) and len(data) > 1 else []
    except Exception:
        pass
    return []


STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
