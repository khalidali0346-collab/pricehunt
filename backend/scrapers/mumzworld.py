"""Mumzworld UAE — #1 baby, kids & maternity store in MENA."""
import httpx, json
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price, make_result

BASE = "https://www.mumzworld.com"

async def scrape(query):
    url = f"{BASE}/en/catalogsearch/result/?q={quote_plus(query)}&product_list_order=price"
    h = get_headers(BASE)
    results = []
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as c:
            r = await c.get(url, headers=h)
        soup = BeautifulSoup(r.text, "lxml")

        for item in soup.select("li.product-item, div.product-item")[:24]:
            title_el = item.select_one("a.product-item-link,[class*='name'],h2,h3")
            price_el = item.select_one("span.price,[class*='price']")
            link_el  = item.select_one("a.product-item-link") or item.select_one("a")
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
                source="Mumzworld", source_type="web", store_type="online",
                url=href, image=img_el.get("src","") or img_el.get("data-src","") if img_el else "",
                location="UAE — Online", shipping="Free delivery over AED 100",
                condition="New",
            ))
    except Exception:
        pass
    return results
