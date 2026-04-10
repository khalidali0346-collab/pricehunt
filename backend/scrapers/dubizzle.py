"""Dubizzle UAE — #1 classifieds for UAE (local + used)."""
import httpx, json, re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, get_api_headers, parse_price, make_result

BASE = "https://uae.dubizzle.com"

CITY_SLUGS = {
    "dubai": "dubai", "abu dhabi": "abu-dhabi", "abudhabi": "abu-dhabi",
    "sharjah": "sharjah", "ajman": "ajman", "ras al khaimah": "ras-al-khaimah",
    "fujairah": "fujairah",
}

def _city(location):
    return CITY_SLUGS.get((location or "dubai").lower().strip(), "dubai")

async def scrape(query, location=None):
    city = _city(location)
    results = []

    # ── Strategy 1: Dubizzle internal API ─────────────────────────
    api_url = (
        f"{BASE}/api/v2/properties/search/"
        f"?keywords={quote_plus(query)}&location={city}&sort_by=price&page_size=24"
    )
    h = get_api_headers(BASE)
    h["Accept"] = "application/json"
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as c:
            r = await c.get(api_url, headers=h)
            if r.status_code == 200:
                data = r.json()
                for item in (data.get("results") or data.get("data") or [])[:24]:
                    title = item.get("title","") or item.get("name","")
                    price = item.get("price") or item.get("amount")
                    imgs  = item.get("images") or item.get("photos") or []
                    img   = imgs[0].get("url","") if imgs and isinstance(imgs[0],dict) else (imgs[0] if imgs else "")
                    href  = item.get("absolute_url") or item.get("url","")
                    loc   = item.get("location",{})
                    loc_str = loc.get("name","") if isinstance(loc,dict) else str(loc or city.title())
                    if not title:
                        continue
                    results.append(make_result(
                        title=title, price=float(price) if price else None,
                        price_text=f"AED {float(price):,.0f}" if price else "Price on request",
                        source="Dubizzle", source_type="local", store_type="physical",
                        url=href if href.startswith("http") else BASE+href,
                        image=img, location=loc_str or city.title(),
                        shipping="Meet seller / Delivery negotiable",
                        condition="Used / As described",
                    ))
                if results:
                    return results
    except Exception:
        pass

    # ── Strategy 2: HTML scrape ────────────────────────────────────
    web_url = f"{BASE}/search/?q={quote_plus(query)}&location={city}"
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as c:
            r = await c.get(web_url, headers=get_headers(BASE))
        soup = BeautifulSoup(r.text, "lxml")

        # Try Next.js data
        script = soup.select_one("script#__NEXT_DATA__")
        if script:
            data = json.loads(script.string)
            listings = (data.get("props",{}).get("pageProps",{})
                        .get("listings") or data.get("props",{})
                        .get("pageProps",{}).get("data",{}).get("results",[]))
            for item in listings[:24]:
                title = item.get("title","") or item.get("name","")
                price = item.get("price") or item.get("amount")
                href  = item.get("url","") or item.get("absolute_url","")
                imgs  = item.get("images",[])
                img   = imgs[0].get("url","") if imgs and isinstance(imgs[0],dict) else ""
                if not title:
                    continue
                results.append(make_result(
                    title=title, price=float(price) if price else None,
                    price_text=f"AED {float(price):,.0f}" if price else "Price on request",
                    source="Dubizzle", source_type="local", store_type="physical",
                    url=href if href.startswith("http") else BASE+href,
                    image=img, location=city.title(),
                    shipping="Meet seller / Delivery negotiable",
                    condition="Used / As described",
                ))
            if results:
                return results

        # Raw HTML cards
        for item in (soup.select("article[data-testid]")
                     or soup.select("li[class*='item']")
                     or soup.select("div[class*='listing']"))[:24]:
            title_el = item.select_one("h2") or item.select_one("h3") or item.select_one("[class*='title']")
            price_el = item.select_one("[class*='price']")
            link_el  = item.select_one("a")
            img_el   = item.select_one("img")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            price = parse_price(price_el.get_text(strip=True)) if price_el else None
            href  = link_el.get("href","") if link_el else ""
            if href and not href.startswith("http"):
                href = BASE + href
            results.append(make_result(
                title=title, price=price,
                price_text=f"AED {price:,.0f}" if price else "Price on request",
                source="Dubizzle", source_type="local", store_type="physical",
                url=href, image=img_el.get("src","") if img_el else "",
                location=city.title(),
                shipping="Meet seller / Delivery negotiable",
                condition="Used / As described",
            ))
    except Exception:
        pass

    return results[:24]
