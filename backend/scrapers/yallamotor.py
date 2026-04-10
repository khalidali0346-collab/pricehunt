"""YallaMotor UAE — cars, SUVs, motorcycles new & used."""
import httpx, json, re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, get_api_headers, parse_price, make_result

BASE = "https://uae.yallamotor.com"

async def scrape(query):
    results = []
    url = f"{BASE}/new-cars/search?q={quote_plus(query)}"
    used_url = f"{BASE}/used-cars/search?q={quote_plus(query)}&sort=price_asc"

    async def _fetch(u, condition):
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=20) as c:
                r = await c.get(u, headers=get_headers(BASE))
            soup = BeautifulSoup(r.text, "lxml")
            # Try Next.js JSON
            script = soup.select_one("script#__NEXT_DATA__")
            if script:
                data = json.loads(script.string)
                cars = (data.get("props",{}).get("pageProps",{}).get("cars")
                        or data.get("props",{}).get("pageProps",{}).get("listings")
                        or data.get("props",{}).get("pageProps",{}).get("data",{}).get("cars",[]))
                for car in (cars or [])[:20]:
                    title = car.get("name") or car.get("title") or f"{car.get('make','')} {car.get('model','')} {car.get('year','')}".strip()
                    price = car.get("price") or car.get("min_price") or car.get("starting_price")
                    img   = car.get("main_image") or car.get("image") or (car.get("images",[None])[0] if car.get("images") else "")
                    href  = car.get("url") or car.get("link","")
                    if not href.startswith("http"):
                        href = BASE + href
                    if not title:
                        continue
                    results.append(make_result(
                        title=title, price=float(price) if price else None,
                        price_text=f"AED {float(price):,.0f}" if price else "Price on request",
                        source="YallaMotor", source_type="web", store_type="both",
                        url=href, image=img if isinstance(img, str) else "",
                        location="UAE — Showrooms & Dealers",
                        shipping="Test drive available", condition=condition,
                    ))
                if results:
                    return

            # HTML fallback
            for item in soup.select("div[class*='car-card'], article[class*='car'], div[class*='listing-item']")[:20]:
                title_el = item.select_one("h2,h3,[class*='name'],[class*='title']")
                price_el = item.select_one("[class*='price']")
                link_el  = item.select_one("a")
                img_el   = item.select_one("img")
                if not title_el:
                    continue
                price = parse_price(price_el.get_text()) if price_el else None
                href  = link_el.get("href","") if link_el else ""
                if href and not href.startswith("http"):
                    href = BASE + href
                results.append(make_result(
                    title=title_el.get_text(strip=True), price=price,
                    price_text=f"AED {price:,.0f}" if price else "Price on request",
                    source="YallaMotor", source_type="web", store_type="both",
                    url=href, image=img_el.get("src","") if img_el else "",
                    location="UAE", shipping="Test drive available", condition=condition,
                ))
        except Exception:
            pass

    await _fetch(used_url, "Used")
    await _fetch(url, "New")
    return results[:24]
