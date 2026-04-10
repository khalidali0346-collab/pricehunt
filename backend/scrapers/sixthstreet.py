"""6th Street UAE — fashion, shoes, accessories."""
import httpx, json
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price, make_result

BASE = "https://en-ae.6thstreet.com"

async def scrape(query):
    results = []
    # 6th Street uses Algolia search
    api = f"https://en-ae.6thstreet.com/search?q={quote_plus(query)}&sort=price_asc"
    h = get_headers(BASE)
    h["Accept-Language"] = "en-AE,en;q=0.9"

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as c:
            r = await c.get(api, headers=h)
        soup = BeautifulSoup(r.text, "lxml")
        script = soup.select_one("script#__NEXT_DATA__")
        if script:
            data = json.loads(script.string)
            hits = (data.get("props",{}).get("pageProps",{})
                    .get("searchResults",{}).get("hits",[])
                    or data.get("props",{}).get("pageProps",{}).get("products",[]))
            for p in hits[:24]:
                title  = p.get("name","") or p.get("title","")
                brand  = p.get("brand","")
                price  = p.get("price_aed") or p.get("price") or p.get("final_price")
                img    = p.get("thumbnail") or p.get("image","")
                url_k  = p.get("url") or p.get("slug","")
                full_title = f"{brand} {title}".strip() if brand else title
                if not full_title or not price:
                    continue
                results.append(make_result(
                    title=full_title, price=float(price),
                    price_text=f"AED {float(price):,.2f}",
                    source="6th Street", source_type="web", store_type="online",
                    url=url_k if url_k.startswith("http") else f"{BASE}/{url_k}",
                    image=img, location="UAE — Online",
                    shipping="Free delivery over AED 100",
                    condition="New",
                ))
            if results:
                return results
    except Exception:
        pass

    # HTML fallback
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as c:
            r = await c.get(api, headers=h)
        soup = BeautifulSoup(r.text, "lxml")
        for item in soup.select("[class*='product'], [class*='item']")[:24]:
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
                source="6th Street", source_type="web", store_type="online",
                url=href, image=img_el.get("src","") if img_el else "",
                location="UAE — Online", shipping="Free delivery over AED 100",
                condition="New",
            ))
    except Exception:
        pass
    return results
