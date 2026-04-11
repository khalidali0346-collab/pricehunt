"""Shared Playwright headless browser for scraping JS-rendered pages."""
import asyncio
from typing import Optional

try:
    from playwright.async_api import async_playwright, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

_playwright = None
_browser: Optional["Browser"] = None
_lock = asyncio.Lock()
_sem = asyncio.Semaphore(4)   # max 4 concurrent pages

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


async def _ensure_browser() -> "Browser":
    global _playwright, _browser
    if _browser and _browser.is_connected():
        return _browser
    async with _lock:
        if _browser and _browser.is_connected():
            return _browser
        if _playwright:
            try:
                await _playwright.stop()
            except Exception:
                pass
        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-gpu",
            ],
        )
    return _browser


async def fetch_rendered(
    url: str,
    wait_selector: str = None,
    extra_wait: float = 2.5,
    timeout: int = 22000,
) -> str:
    """
    Load *url* in a headless Chromium tab, wait for JS to render,
    and return the full HTML string.  Returns '' on any failure.
    """
    if not PLAYWRIGHT_AVAILABLE:
        return ""
    async with _sem:
        try:
            browser = await _ensure_browser()
            ctx = await browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent=_UA,
                locale="en-AE",
                timezone_id="Asia/Dubai",
                extra_http_headers={
                    "Accept-Language": "en-AE,en;q=0.9",
                    "Accept": (
                        "text/html,application/xhtml+xml,"
                        "application/xml;q=0.9,*/*;q=0.8"
                    ),
                },
            )
            page = await ctx.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
                if wait_selector:
                    try:
                        await page.wait_for_selector(wait_selector, timeout=8000)
                    except Exception:
                        pass  # Best-effort — continue with whatever loaded
                await asyncio.sleep(extra_wait)
                return await page.content()
            finally:
                await ctx.close()
        except Exception:
            return ""
