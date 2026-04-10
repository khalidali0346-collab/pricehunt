"""Ounass UAE — luxury fashion & lifestyle (The Net-a-Porter of the Middle East)."""
import httpx, json
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price, make_result

BASE = "https://www.ounass.ae"

async def scrape(query):
    url = f"{BASE}/search?q={quote_plus(query)}&sort=price_asc"
    h = get_headers(BASE)
    results = []
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as c:
            r = await c.get(url, headers=h)
        soup = BeautifulSoup(r.text, "lxml")
        script = soup.select_one("script#__NEXT_DATA__")
        if script:
            data = json.loads(script.string)
            prods = (data.get("props",{}).get("pageProps",{}).get("products",[])
                     or data.get("props",{}).get("pageProps",{}).get("catalog",{}).get("hits",[]))
            for p in prods[:24]:
                title  = p.get("name","") or p.get("title","")
                brand  = p.get("brand","") or p.get("designer","")
                price  = p.get("price") or p.get("salePrice") or p.get("priceAED")
                img    = p.get("image","") or p.get("thumbnail","")
                slug   = p.get("url","") or p.get("slug","")
                full   = f"{brand} — {title}".strip(" —") if brand else title
                if not full or not price:
                    continue
                results.append(make_result(
                    title=full, price=float(price),
                    price_text=f"AED {float(price):,.2f}",
                    source="Ounass", source_type="web", store_type="online",
                    url=slug if slug.startswith("http") else BASE+slug,
                    image=img, location="UAE — Luxury Delivery",
                    shipping="Same-day & next-day delivery",
                    condition="New",
                ))
            if results:
                return results

        # HTML fallback
        for item in soup.select("[class*='product'],[class*='item']")[:24]:
            title_el = item.select_one("[class*='name'],[class*='title'],h2,h3")
            price_el = item.select_one("[class*='price']")
            link_el  = item.select_one("a")
            img_el   = item.select_one("img")
            if not title_el or not price_el:
                continue
            price = parse_price(price_el.get_text())
            if not price:
                continue
            href = link_el.get("href","") if link_el else ""
            if href and not href.startswith("http"):
                href = BASE + href
            results.append(make_result(
                title=title_el.get_text(strip=True), price=price,
                price_text=f"AED {price:,.2f}",
                source="Ounass", source_type="web", store_type="online",
                url=href, image=img_el.get("src","") if img_el else "",
                location="UAE — Luxury", shipping="Same/next-day delivery",
                condition="New",
            ))
    except Exception:
        pass
    return results
