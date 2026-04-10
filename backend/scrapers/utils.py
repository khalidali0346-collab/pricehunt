import re, random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
]

def get_headers(referer="https://www.google.com"):
    ua = random.choice(USER_AGENTS)
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-AE,en-US;q=0.9,en;q=0.8,ar;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": referer,
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Cache-Control": "max-age=0",
    }

def get_api_headers(referer="https://www.google.com"):
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-AE,en-US;q=0.9,en;q=0.8",
        "Referer": referer,
        "DNT": "1",
        "Connection": "keep-alive",
    }

def parse_price(text):
    if not text:
        return None
    text = str(text).replace(",", "").replace("\u00a0", " ")
    # Remove currency words
    text = re.sub(r"(AED|aed|د\.إ|dhs?|SAR|KWD|QAR|USD|\$|€|£)", " ", text, flags=re.I)
    match = re.search(r"(\d+(?:\.\d{1,2})?)", text)
    if match:
        try:
            v = float(match.group(1))
            return v if v > 0 else None
        except ValueError:
            return None
    return None

def make_result(title, price, price_text, source, source_type, url,
                image=None, location=None, shipping=None, condition=None,
                currency="AED", rating=None, store_type="online"):
    return {
        "title": title or "",
        "price": price,
        "price_text": price_text or (f"AED {price:,.2f}" if price else "Price on request"),
        "source": source,
        "source_type": source_type,
        "store_type": store_type,   # "online" | "physical" | "both"
        "url": url or "",
        "image": image or "",
        "location": location or "",
        "shipping": shipping or "",
        "condition": condition or "New",
        "currency": currency,
        "rating": rating or "",
    }
