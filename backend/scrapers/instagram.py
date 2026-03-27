"""Instagram scraper — searches public hashtag pages for price-tagged posts."""
import httpx
import json
import re
from urllib.parse import quote_plus
from .utils import get_headers, parse_price


async def scrape(query: str) -> list[dict]:
    # Build hashtag from query (no spaces, lowercase)
    tag = re.sub(r"[^a-zA-Z0-9]", "", query.lower())
    results = []

    # Try Instagram's public GraphQL endpoint for hashtag media
    url = f"https://www.instagram.com/explore/tags/{tag}/?__a=1&__d=dis"
    headers = get_headers("https://www.instagram.com")
    headers["X-IG-App-ID"] = "936619743392459"

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
            r = await client.get(url, headers=headers)
            if r.status_code == 200:
                data = r.json()
                edges = (
                    data.get("graphql", {})
                    .get("hashtag", {})
                    .get("edge_hashtag_to_media", {})
                    .get("edges", [])
                )
                for edge in edges[:20]:
                    node = edge.get("node", {})
                    caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
                    caption = caption_edges[0]["node"]["text"] if caption_edges else ""

                    # Only include posts that mention a price
                    price_match = re.search(r"\$\s*[\d,]+(?:\.\d{1,2})?", caption)
                    if not price_match:
                        continue

                    price_text = price_match.group(0).replace(" ", "")
                    price = parse_price(price_text)

                    # First line of caption as title
                    title = caption.split("\n")[0][:80] or f"#{tag} listing"

                    shortcode = node.get("shortcode", "")
                    post_url = f"https://www.instagram.com/p/{shortcode}/"

                    thumbnail = (
                        node.get("thumbnail_src")
                        or node.get("display_url")
                        or ""
                    )

                    results.append(
                        {
                            "title": title,
                            "price": price,
                            "price_text": price_text,
                            "source": "Instagram",
                            "source_type": "instagram",
                            "url": post_url,
                            "image": thumbnail,
                            "location": None,
                            "shipping": "DM seller for details",
                            "condition": "See post",
                        }
                    )
    except Exception:
        pass

    # Fallback: try web scrape of the hashtag page for embedded JSON
    if not results:
        try:
            url2 = f"https://www.instagram.com/explore/tags/{tag}/"
            headers2 = get_headers("https://www.instagram.com")
            async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
                r2 = await client.get(url2, headers=headers2)
                text = r2.text
                # Extract shared_data JSON
                match = re.search(r"window\._sharedData\s*=\s*({.+?});</script>", text)
                if match:
                    shared = json.loads(match.group(1))
                    media = (
                        shared.get("entry_data", {})
                        .get("TagPage", [{}])[0]
                        .get("graphql", {})
                        .get("hashtag", {})
                        .get("edge_hashtag_to_media", {})
                        .get("edges", [])
                    )
                    for edge in media[:20]:
                        node = edge.get("node", {})
                        caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
                        caption = caption_edges[0]["node"]["text"] if caption_edges else ""
                        price_match = re.search(r"\$\s*[\d,]+(?:\.\d{1,2})?", caption)
                        if not price_match:
                            continue
                        price_text = price_match.group(0).replace(" ", "")
                        price = parse_price(price_text)
                        title = caption.split("\n")[0][:80] or f"#{tag} listing"
                        shortcode = node.get("shortcode", "")
                        results.append(
                            {
                                "title": title,
                                "price": price,
                                "price_text": price_text,
                                "source": "Instagram",
                                "source_type": "instagram",
                                "url": f"https://www.instagram.com/p/{shortcode}/",
                                "image": node.get("thumbnail_src", ""),
                                "location": None,
                                "shipping": "DM seller for details",
                                "condition": "See post",
                            }
                        )
        except Exception:
            pass

    return results
