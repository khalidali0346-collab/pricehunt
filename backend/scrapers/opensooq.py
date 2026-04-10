"""OpenSooq — largest MENA classifieds platform."""
import httpx, json, re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, get_api_headers, parse_price, make_result

COUNTRY_MAP = {
    "uae":"ae","dubai":"ae","abu dhabi":"ae","sharjah":"ae","ajman":"ae",
    "saudi arabia":"sa","ksa":"sa","riyadh":"sa","jeddah":"sa",
    "kuwait":"kw","qatar":"qa","doha":"qa","bahrain":"bh",
    "oman":"om","muscat":"om","jordan":"jo","amman":"jo",
    "egypt":"eg","cairo":"eg","lebanon":"lb","beirut":"lb",
}

CURRENCY_MAP = {"ae":"AED","sa":"SAR","kw":"KWD","qa":"QAR","bh":"BHD","om":"OMR","jo":"JOD","eg":"EGP","lb":"LBP"}

def _country(loc):
    return COUNTRY_MAP.get((loc or "uae").lower().strip(), "ae")

async def scrape(query, location=None):
    cc  = _country(location)
    cur = CURRENCY_MAP.get(cc, "AED")
    results = []

    # ── Strategy 1: API ───────────────────────────────────────────
    api = f"https://{cc}.opensooq.com/api/listing/search?term={quote_plus(query)}&sort=price_asc&limit=24"
    h   = get_api_headers(f"https://{cc}.opensooq.com")
    h["Accept"] = "application/json"
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as c:
            r = await c.get(api, headers=h)
            if r.status_code == 200:
                data = r.json()
                listings = data.get("data",{}).get("listings") or data.get("listings") or data.get("data",[])
                for item in listings[:24]:
                    title = item.get("title","") or item.get("name","")
                    price = item.get("price") or item.get("amount")
                    href  = item.get("url","") or item.get("full_url","")
                    img   = (item.get("images",[{}])[0] or {}).get("src","")
                    loc_s = item.get("city","") or item.get("location","") or (location or cc.upper())
                    if not title:
                        continue
                    results.append(make_result(
                        title=title, price=float(price) if price else None,
                        price_text=f"{cur} {float(price):,.0f}" if price else "Price on request",
                        source="OpenSooq", source_type="local", store_type="physical",
                        url=href if href.startswith("http") else f"https://{cc}.opensooq.com{href}",
                        image=img, location=str(loc_s),
                        shipping="Contact seller",
                        condition="Used / As described",
                        currency=cur,
                    ))
                if results:
                    return results
    except Exception:
        pass

    # ── Strategy 2: HTML scrape ────────────────────────────────────
    web = f"https://{cc}.opensooq.com/search?term={quote_plus(query)}&sort=price_asc"
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as c:
            r = await c.get(web, headers=get_headers(f"https://{cc}.opensooq.com"))
        soup = BeautifulSoup(r.text, "lxml")

        items = (soup.select("li.post-cell") or soup.select("div[class*='post-cell']")
                 or soup.select("article") or soup.select("div[class*='listing']"))
        for item in items[:24]:
            title_el = item.select_one("h2,h3,[class*='title'],[class*='name']")
            price_el = item.select_one("[class*='price'],strong")
            link_el  = item.select_one("a")
            img_el   = item.select_one("img")
            loc_el   = item.select_one("[class*='location'],[class*='city']")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            price = parse_price(price_el.get_text(strip=True)) if price_el else None
            href  = link_el.get("href","") if link_el else ""
            if href and not href.startswith("http"):
                href = f"https://{cc}.opensooq.com{href}"
            results.append(make_result(
                title=title, price=price,
                price_text=f"{cur} {price:,.0f}" if price else "Price on request",
                source="OpenSooq", source_type="local", store_type="physical",
                url=href, image=img_el.get("src","") or img_el.get("data-src","") if img_el else "",
                location=loc_el.get_text(strip=True) if loc_el else (location or cc.upper()),
                shipping="Contact seller", condition="Used / As described", currency=cur,
            ))
    except Exception:
        pass

    return results[:24]
