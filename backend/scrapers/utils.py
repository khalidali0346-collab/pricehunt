import re
import random

USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    # Chrome on Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:125.0) Gecko/20100101 Firefox/125.0",
    # Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
]

_SEC_FETCH_SITE = ["none", "same-origin", "cross-site"]


def get_headers(referer: str = "https://www.google.com") -> dict:
    ua = random.choice(USER_AGENTS)
    is_chrome = "Chrome" in ua and "Edg" not in ua
    is_firefox = "Firefox" in ua
    is_edge = "Edg" in ua

    base = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
        "Referer": referer,
    }

    if is_chrome or is_edge:
        base.update({
            "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        })
    elif is_firefox:
        base.update({
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "DNT": "1",
        })

    return base


def parse_price(text: str) -> float | None:
    """Extract the first numeric price value from a string.

    Handles formats like:
      AED 1,299.00 / AED1299 / $29.99 / 29.99 USD / 1.299,00 (European)
    """
    if not text:
        return None

    # Normalise: strip known currency symbols/codes to isolate the number
    cleaned = re.sub(
        r'(?:AED|USD|SAR|KWD|QAR|BHD|OMR|EGP|GBP|EUR|د\.إ|ر\.س|dhs?|Dhs?|kr|₹|€|£|\$)',
        '', text, flags=re.IGNORECASE
    ).strip()

    # Remove thousands separators (commas followed by 3 digits) but keep decimal
    # Handle both 1,299.00 and European 1.299,00 formats
    # Detect European format: ends with ,XX (1-2 decimal digits)
    if re.search(r'\d{1,3}(?:\.\d{3})+,\d{1,2}$', cleaned):
        # European format: swap . and ,
        cleaned = cleaned.replace(".", "").replace(",", ".")
    else:
        cleaned = cleaned.replace(",", "")

    match = re.search(r'(\d+(?:\.\d{1,2})?)', cleaned)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None
