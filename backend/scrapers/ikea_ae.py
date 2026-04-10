"""IKEA UAE — furniture and home furnishings."""
import httpx, json
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price, make_result

BASE = "https://www.ikea.com/ae/en"

async def scrape(query):
    # IKEA has an internal search API
    api = f"https://sik.search.blue.cdtapps.com/ae/en/search-result-page?q={quote_plus(query)}&size=24&c=sr&sort=price-asc&v=20211018"
    h = get_headers(BASE)
    h["Accept"] = "application/json"
    results = []

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as c:
            r = await c.get(api, headers=h)
            if r.status_code == 200:
                data = r.json()
                products = (data.get("searchResultPage",{}).get("productWindow",[])
                            or data.get("products",[]))
                for p in products[:24]:
                    name = p.get("name","")
                    typ  = p.get("typeName","")
                    title = f"{name} {typ}".strip() if typ else name
                    price_info = p.get("salesPrice") or p.get("price") or {}
                    price = price_info.get("numeral") or price_info.get("value") if isinstance(price_info, dict) else price_info
                    img   = p.get("mainImageUrl") or p.get("imageUrl","")
                    href  = f"{BASE}/products/{p.get('id','').lower()}/"
                    if not title:
                        continue
                    results.append(make_result(
                        title=title, price=float(str(price).replace(",","")) if price else None,
                        price_text=f"AED {float(str(price).replace(',','')):,.2f}" if price else "See store",
                        source="IKEA UAE", source_type="web", store_type="both",
                        url=href, image=img,
                        location="UAE — Festival City, Yas Island & more",
                        shipping="Home delivery / Click & Collect",
                        condition="New",
                    ))
                if results:
                    return results
    except Exception:
        pass

    # Web fallback
    try:
        web = f"{BASE}/search/?q={quote_plus(query)}"
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as c:
            r = await c.get(web, headers=get_headers(BASE))
        soup = BeautifulSoup(r.text, "lxml")
        for item in soup.select("[class*='product'], [class*='plp-fragment']")[:24]:
            title_el = item.select_one("[class*='name']") or item.select_one("h2,h3")
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
                source="IKEA UAE", source_type="web", store_type="both",
                url=href, image=img_el.get("src","") if img_el else "",
                location="UAE — In-store & online",
                shipping="Home delivery / Click & Collect",
                condition="New",
            ))
    except Exception:
        pass

    return results
