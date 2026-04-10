"""Sharaf DG — leading UAE electronics retailer (physical + online)."""
import httpx, json
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price, make_result

BASE = "https://www.sharafdg.com"

async def scrape(query):
    results = []
    url = f"{BASE}/search?q={quote_plus(query)}&sort=price+asc"
    h = get_headers(BASE)
    h["Accept-Language"] = "en-AE,en;q=0.9"

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=25) as c:
            r = await c.get(url, headers=h)
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "lxml")

    # Try embedded JSON (Magento 2 page_data)
    for script in soup.find_all("script", type="text/x-magento-init"):
        try:
            data = json.loads(script.string or "{}")
            # Magento stores product data in various keys
            for key in ["*", "[data-role=msrp-popup]"]:
                items = data.get(key, {})
                for comp_key, comp_val in items.items():
                    if "product" in comp_key.lower() and isinstance(comp_val, dict):
                        prods = comp_val.get("products") or comp_val.get("items") or []
                        for p in prods[:24]:
                            title = p.get("name","")
                            price = p.get("price_range",{}).get("minimum_price",{}).get("final_price",{}).get("value")
                            if not title or not price:
                                continue
                            results.append(make_result(
                                title=title, price=float(price),
                                price_text=f"AED {float(price):,.2f}",
                                source="Sharaf DG", source_type="web", store_type="both",
                                url=p.get("url_key",""), image=p.get("small_image",{}).get("url",""),
                                location="UAE — 65+ stores",
                                shipping="Home Delivery / In-store pickup",
                                condition="New",
                            ))
                        if results:
                            return results
        except Exception:
            continue

    # HTML parse
    for item in soup.select("li.product-item, div.product-item, div[class*='product-card']")[:24]:
        title_el = (item.select_one("a.product-item-link")
                    or item.select_one("[class*='product-name']") or item.select_one("h2,h3"))
        price_el  = item.select_one("span.price") or item.select_one("[class*='price']")
        link_el   = item.select_one("a.product-item-link") or item.select_one("a")
        img_el    = item.select_one("img.product-image-photo") or item.select_one("img")

        if not title_el or not price_el:
            continue
        price = parse_price(price_el.get_text(strip=True))
        if not price:
            continue
        href = link_el.get("href","") if link_el else ""
        if href and not href.startswith("http"):
            href = BASE + href
        results.append(make_result(
            title=title_el.get_text(strip=True), price=price,
            price_text=f"AED {price:,.2f}",
            source="Sharaf DG", source_type="web", store_type="both",
            url=href, image=img_el.get("src","") or img_el.get("data-src","") if img_el else "",
            location="UAE — 65+ stores",
            shipping="Home Delivery / In-store pickup",
            condition="New",
        ))
    return results[:24]
