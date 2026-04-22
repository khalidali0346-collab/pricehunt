"""Shared browser utility — Playwright if available, httpx fallback otherwise."""
import asyncio
from typing import Optional

try:
    from playwright.async_api import async_playwright, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

import httpx
from .utils import get_headers

_playwright = None
_browser: Optional["Browser"] = None
_lock = asyncio.Lock()
_sem = asyncio.Semaphore(4)

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


async def _playwright_fetch(url: str, wait_selector: str, extra_wait: float, timeout: int) -> str:
    global _playwright, _browser
    if _browser and _browser.is_connected():
        b = _browser
    else:
        async with _lock:
            if _browser and _browser.is_connected():
                b = _browser
            else:
                if _playwright:
                    try:
                        await _playwright.stop()
                    except Exception:
                        pass
                _playwright = await async_playwright().start()
                _browser = await _playwright.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox", "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-gpu",
                    ],
                )
                b = _browser

    ctx = await b.new_context(
        viewport={"width": 1366, "height": 768},
        user_agent=_UA,
        locale="en-AE",
        timezone_id="Asia/Dubai",
        extra_http_headers={"Accept-Language": "en-AE,en;q=0.9"},
    )
    page = await ctx.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        if wait_selector:
            try:
                await page.wait_for_selector(wait_selector, timeout=8000)
            except Exception:
                pass
        await asyncio.sleep(extra_wait)
        return await page.content()
    finally:
        await ctx.close()


async def fetch_rendered(
    url: str,
    wait_selector: str = None,
    extra_wait: float = 2.5,
    timeout: int = 22000,
) -> str:
    """
    Fetch a page with JS execution (Playwright) when available,
    falling back to plain httpx so scrapers always get a chance.
    """
    async with _sem:
        # ── Playwright path ───────────────────────────────────
        if PLAYWRIGHT_AVAILABLE:
            try:
                return await _playwright_fetch(url, wait_selector, extra_wait, timeout)
            except Exception:
                pass  # Fall through to httpx

        # ── httpx fallback ────────────────────────────────────
        try:
            headers = get_headers(url)
            headers["Accept-Language"] = "en-AE,en;q=0.9"
            async with httpx.AsyncClient(follow_redirects=True, timeout=25) as client:
                r = await client.get(url, headers=headers)
                if r.status_code == 200:
                    return r.text
        except Exception:
            pass

        return ""
