"""Walmart scraper."""
import httpx
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .utils import get_headers, parse_price


async def scrape(query: str) -> list[dict]:
    url = f"https://www.walmart.com/search?q={quote_plus(query)}&sort=price_low"
    headers = get_headers("https://www.walmart.com")
    headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "lxml")
    results = []

    # Walmart embeds product data as JSON in <script type="application/json">
    for script in soup.select('script[type="application/json"]'):
        try:
            data = json.loads(script.string or "")
            items = (
                data.get("props", {})
                .get("pageProps", {})
                .get("initialData", {})
                .get("searchResult", {})
                .get("itemStacks", [{}])[0]
                .get("items", [])
            )
            for it in items[:20]:
                title = it.get("name", "")
                price_info = it.get("priceInfo", {})
                price_val = price_info.get("currentPrice", {}).get("price")
                price_text = price_info.get("currentPrice", {}).get("priceString", "")
                item_url = "https://www.walmart.com" + it.get("canonicalUrl", "")
                img = it.get("imageInfo", {}).get("thumbnailUrl", "")

                if not title or price_val is None:
                    continue

                results.append(
                    {
                        "title": title,
                        "price": float(price_val),
                        "price_text": price_text or f"${price_val:,.2f}",
                        "source": "Walmart",
                        "source_type": "web",
                        "url": item_url,
                        "image": img,
                        "location": None,
                        "shipping": it.get("fulfillmentSummary", [{}])[0].get("fulfillmentType", ""),
                        "condition": "New",
                    }
                )
            if results:
                break
        except (json.JSONDecodeError, IndexError, TypeError, KeyError):
            continue

    # HTML fallback
    if not results:
        for item in soup.select("div[data-item-id]")[:20]:
            title_el = item.select_one("span.lh-title")
            price_el = item.select_one("div.price-main") or item.select_one("[itemprop='price']")
            link_el = item.select_one("a")
            img_el = item.select_one("img")

            if not title_el or not price_el:
                continue

            title = title_el.get_text(strip=True)
            price_text = price_el.get_text(strip=True)
            price = parse_price(price_text)
            if not price:
                continue

            href = link_el.get("href", "") if link_el else ""
            if href.startswith("/"):
                href = "https://www.walmart.com" + href

            results.append(
                {
                    "title": title,
                    "price": price,
                    "price_text": f"${price:,.2f}",
                    "source": "Walmart",
                    "source_type": "web",
                    "url": href,
                    "image": img_el.get("src", "") if img_el else None,
                    "location": None,
                    "shipping": None,
                    "condition": "New",
                }
            )

    return results
