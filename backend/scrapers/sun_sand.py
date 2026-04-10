"""Sun & Sand Sports UAE — largest sports retailer in MENA."""
import httpx, json
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price, make_result

BASE = "https://www.sssports.com"

async def scrape(query):
    url = f"{BASE}/en-ae/search?q={quote_plus(query)}&prefn1=is-available&prefv1=true&srule=sort-price-ascending"
    h = get_headers(BASE)
    results = []

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as c:
            r = await c.get(url, headers=h)
        soup = BeautifulSoup(r.text, "lxml")

        # Try embedded JSON
        for script in soup.find_all("script", type="application/json"):
            try:
                data = json.loads(script.string or "{}")
                prods = data.get("products") or data.get("hits") or []
                for p in prods[:24]:
                    title  = p.get("name","") or p.get("title","")
                    price  = p.get("price") or p.get("salePrice")
                    img    = p.get("image","") or p.get("images",[""])[0]
                    href   = p.get("url","") or p.get("pdpUrl","")
                    if not title or not price:
                        continue
                    if not href.startswith("http"):
                        href = BASE + href
                    results.append(make_result(
                        title=title, price=float(price),
                        price_text=f"AED {float(price):,.2f}",
                        source="Sun & Sand Sports", source_type="web", store_type="both",
                        url=href, image=img,
                        location="UAE — 60+ stores in MENA",
                        shipping="Home Delivery / Store pickup",
                        condition="New",
                    ))
                if results:
                    return results
            except Exception:
                continue

        # HTML fallback
        for item in soup.select(".product-tile, [class*='product-grid-tile']")[:24]:
            title_el = item.select_one(".product-name, [class*='name']")
            price_el = item.select_one(".price, [class*='price']")
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
                source="Sun & Sand Sports", source_type="web", store_type="both",
                url=href, image=img_el.get("src","") if img_el else "",
                location="UAE — 60+ stores",
                shipping="Home Delivery / Store pickup",
                condition="New",
            ))
    except Exception:
        pass
    return results
