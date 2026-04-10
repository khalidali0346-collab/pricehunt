"""Emax — UAE electronics retail chain (physical stores + online)."""
import httpx, json
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price, make_result

BASE = "https://www.emax.ae"

async def scrape(query):
    url = f"{BASE}/catalogsearch/result/?q={quote_plus(query)}&product_list_order=price"
    h = get_headers(BASE)
    results = []
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=25) as c:
            r = await c.get(url, headers=h)
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "lxml")

    for item in soup.select("li.product-item, div.product-item")[:24]:
        title_el = (item.select_one("a.product-item-link")
                    or item.select_one("[class*='name']") or item.select_one("h2,h3"))
        price_el  = item.select_one("span.price") or item.select_one("[class*='price']")
        link_el   = item.select_one("a.product-item-link") or item.select_one("a")
        img_el    = item.select_one("img")
        if not title_el or not price_el:
            continue
        price = parse_price(price_el.get_text(strip=True))
        if not price:
            continue
        href = link_el.get("href","") if link_el else ""
        if href and not href.startswith("http"):
            href = BASE + href
        img_src = img_el.get("src","") or img_el.get("data-src","") if img_el else ""
        results.append(make_result(
            title=title_el.get_text(strip=True), price=price,
            price_text=f"AED {price:,.2f}",
            source="Emax", source_type="web", store_type="both",
            url=href, image=img_src,
            location="UAE — Physical stores across Emirates",
            shipping="Home Delivery / Store pickup",
            condition="New",
        ))
    return results
