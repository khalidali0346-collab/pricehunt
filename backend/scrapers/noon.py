"""Noon.com — largest MENA e-commerce platform."""
import httpx, json
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, get_api_headers, parse_price, make_result

BASE = "https://www.noon.com"

async def scrape(query):
    results = []

    # ── Strategy 1: internal catalog API ──────────────────────────
    api = f"{BASE}/uae-en/search/?q={quote_plus(query)}&sortBy=price_asc"
    h = get_headers(BASE)
    h["Accept-Language"] = "en-AE,en;q=0.9"

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=25) as c:
            r = await c.get(api, headers=h)

        soup = BeautifulSoup(r.text, "lxml")
        script = soup.select_one("script#__NEXT_DATA__")
        if script:
            data = json.loads(script.string)
            hits = (data.get("props",{}).get("pageProps",{})
                    .get("catalog",{}).get("hits",[]))
            for p in hits[:24]:
                price = p.get("sale_price") or p.get("price") or p.get("regular_price")
                title = p.get("name","")
                brand = p.get("brand","")
                sku   = p.get("sku","")
                imgs  = p.get("image_keys",[])
                img   = f"https://f.nooncdn.com/p/{imgs[0]}?format=avif" if imgs else ""
                if not title or not price:
                    continue
                full_title = f"{brand} {title}".strip() if brand else title
                results.append(make_result(
                    title=full_title, price=float(price),
                    price_text=f"AED {float(price):,.2f}",
                    source="Noon", source_type="web", store_type="online",
                    url=f"{BASE}/uae-en/{sku}/", image=img,
                    location="UAE — Noon Express",
                    shipping="Noon Express delivery",
                ))
            if results:
                return results
    except Exception:
        pass

    # ── Strategy 2: HTML card parse ───────────────────────────────
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=25) as c:
            r = await c.get(api, headers=h)
        soup = BeautifulSoup(r.text, "lxml")
        for item in soup.select("div[class*='sc-']")[:30]:
            title_el = item.select_one("[class*='name']") or item.select_one("h3")
            price_el = item.select_one("[class*='price']") or item.select_one("strong")
            link_el  = item.select_one("a")
            img_el   = item.select_one("img")
            if not title_el or not price_el:
                continue
            title = title_el.get_text(strip=True)
            price = parse_price(price_el.get_text(strip=True))
            if not title or not price:
                continue
            href = link_el.get("href","") if link_el else ""
            if href and not href.startswith("http"):
                href = BASE + href
            results.append(make_result(
                title=title, price=price, price_text=f"AED {price:,.2f}",
                source="Noon", source_type="web", store_type="online",
                url=href, image=img_el.get("src","") if img_el else "",
                location="UAE", shipping="Noon Express",
            ))
    except Exception:
        pass

    return results[:24]
