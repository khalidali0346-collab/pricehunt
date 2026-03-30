"""Instagram UAE scraper — searches hashtags and public posts for price listings."""
import httpx, json, re
from urllib.parse import quote_plus
from .utils import get_headers, parse_price


def _build_tags(query: str) -> list[str]:
    base = re.sub(r"[^a-zA-Z0-9 ]", "", query).strip()
    words = base.split()
    tags = []
    # exact phrase tag
    tags.append("".join(words).lower())
    # with UAE/Dubai suffix
    tags.append("".join(words).lower() + "uae")
    tags.append("".join(words).lower() + "dubai")
    # forsale variants
    tags.append("".join(words).lower() + "forsale")
    return tags[:4]


async def _fetch_tag(tag: str, client: httpx.AsyncClient) -> list[dict]:
    results = []
    url = f"https://www.instagram.com/explore/tags/{tag}/?__a=1&__d=dis"
    headers = get_headers("https://www.instagram.com")
    headers["X-IG-App-ID"] = "936619743392459"
    try:
        r = await client.get(url, headers=headers)
        if r.status_code == 200:
            data = r.json()
            edges = (
                data.get("graphql", {}).get("hashtag", {})
                .get("edge_hashtag_to_media", {}).get("edges", [])
            )
            for edge in edges:
                node = edge.get("node", {})
                cap_edges = node.get("edge_media_to_caption", {}).get("edges", [])
                caption = cap_edges[0]["node"]["text"] if cap_edges else ""
                price_match = re.search(r"(?:AED|aed|د\.إ|dhs?|Dhs?)[\s]*([0-9][0-9,\.]*)", caption, re.I)
                if not price_match:
                    price_match = re.search(r"\$\s*([0-9][0-9,\.]*)", caption)
                if not price_match:
                    continue
                raw_price = price_match.group(0)
                price = parse_price(raw_price)
                title = caption.split("\n")[0][:100] or f"#{tag} listing"
                shortcode = node.get("shortcode", "")
                results.append({
                    "title": title,
                    "price": price,
                    "price_text": f"AED {price:,.0f}" if price else raw_price,
                    "source": "Instagram",
                    "source_type": "instagram",
                    "url": f"https://www.instagram.com/p/{shortcode}/",
                    "image": node.get("thumbnail_src") or node.get("display_url", ""),
                    "location": "UAE (Instagram seller)",
                    "shipping": "DM seller for details",
                    "condition": "See post",
                    "currency": "AED",
                })
    except Exception:
        pass
    return results


async def scrape(query: str) -> list[dict]:
    tags = _build_tags(query)
    results = []
    seen_urls = set()
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
            for tag in tags:
                tag_results = await _fetch_tag(tag, client)
                for r in tag_results:
                    if r["url"] not in seen_urls:
                        seen_urls.add(r["url"])
                        results.append(r)
    except Exception:
        pass
    return results[:20]
