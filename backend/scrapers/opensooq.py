"""OpenSooq scraper — largest classifieds platform in MENA."""
import httpx
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price

COUNTRY_MAP = {
    "uae": "ae",
    "dubai": "ae",
    "abu dhabi": "ae",
    "sharjah": "ae",
    "saudi arabia": "sa",
    "ksa": "sa",
    "riyadh": "sa",
    "jeddah": "sa",
    "kuwait": "kw",
    "qatar": "qa",
    "doha": "qa",
    "bahrain": "bh",
    "oman": "om",
    "muscat": "om",
    "jordan": "jo",
    "amman": "jo",
    "egypt": "eg",
    "cairo": "eg",
    "lebanon": "lb",
    "beirut": "lb",
}

DEFAULT_COUNTRY = "ae"


def resolve_country(location: str | None) -> str:
    if not location:
        return DEFAULT_COUNTRY
    key = location.lower().strip()
    return COUNTRY_MAP.get(key, DEFAULT_COUNTRY)


async def scrape(query: str, location: str | None = None) -> list[dict]:
    country = resolve_country(location)
    url = f"https://{country}.opensooq.com/search?term={quote_plus(query)}&sort=price_asc"
    headers = get_headers(f"https://{country}.opensooq.com")
    headers["Accept-Language"] = "en,ar;q=0.9"

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "lxml")
    results = []

    currency = "AED" if country == "ae" else "SAR" if country == "sa" else "USD"

    items = (
        soup.select("li.post-cell")
        or soup.select("div[class*='post-cell']")
        or soup.select("div[class*='listing-item']")
        or soup.select("article")
    )

    for item in items[:24]:
        title_el = (
            item.select_one("h2")
            or item.select_one("h3")
            or item.select_one("[class*='title']")
            or item.select_one("[class*='name']")
        )
        price_el = (
            item.select_one("[class*='price']")
            or item.select_one("strong")
        )
        link_el = item.select_one("a")
        img_el = item.select_one("img")
        location_el = item.select_one("[class*='location']") or item.select_one("[class*='city']")

        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        if not title:
            continue

        price_text = price_el.get_text(strip=True) if price_el else ""
        price = parse_price(price_text)

        href = link_el.get("href", "") if link_el else ""
        if href and not href.startswith("http"):
            href = f"https://{country}.opensooq.com" + href

        loc_text = location_el.get_text(strip=True) if location_el else (location or "UAE")

        results.append({
            "title": title,
            "price": price,
            "price_text": f"{currency} {price:,.0f}" if price else price_text or "Price on request",
            "source": "OpenSooq",
            "source_type": "local",
            "url": href,
            "image": img_el.get("src", "") or img_el.get("data-src", "") if img_el else None,
            "location": loc_text,
            "shipping": "Contact seller",
            "condition": "Used/New",
            "currency": currency,
        })

    return results
