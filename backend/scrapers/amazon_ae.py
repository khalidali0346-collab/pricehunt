"""Amazon.ae scraper — UAE Amazon store."""
import httpx
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price


async def scrape(query: str) -> list[dict]:
    url = f"https://www.amazon.ae/s?k={quote_plus(query)}&s=price-asc-rank"
    headers = get_headers("https://www.amazon.ae")
    headers["Accept-Language"] = "en-AE,en;q=0.9"

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=25) as client:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "lxml")
    results = []

    for item in soup.select("div[data-component-type='s-search-result']")[:20]:
        title_el = item.select_one("h2 a span") or item.select_one("h2 span")
        price_whole = item.select_one("span.a-price-whole")
        price_fraction = item.select_one("span.a-price-fraction")
        link_el = item.select_one("h2 a") or item.select_one("a.a-link-normal")
        img_el = item.select_one("img.s-image")
        rating_el = item.select_one("span.a-icon-alt")

        if not title_el or not price_whole:
            continue

        title = title_el.get_text(strip=True)
        fraction = price_fraction.get_text(strip=True) if price_fraction else "00"
        price_text = f"AED {price_whole.get_text(strip=True)}{fraction}"
        price = parse_price(price_text)

        href = link_el.get("href", "") if link_el else ""
        if href and not href.startswith("http"):
            href = "https://www.amazon.ae" + href

        results.append({
            "title": title,
            "price": price,
            "price_text": price_text,
            "source": "Amazon.ae",
            "source_type": "web",
            "url": href,
            "image": img_el.get("src", "") if img_el else None,
            "location": "UAE",
            "shipping": "Fulfilled by Amazon",
            "condition": "New",
            "currency": "AED",
            "rating": rating_el.get_text(strip=True) if rating_el else None,
        })

    return results
