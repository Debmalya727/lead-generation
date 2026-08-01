import asyncio
import logging
import random
import urllib.parse
from typing import List

from app.modules.discovery.providers.base_provider import BaseDiscoveryProvider
from app.modules.discovery.providers.search_helper import fetch_real_directory_leads

logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None


class GoogleMapsProvider(BaseDiscoveryProvider):
    def __init__(self):
        super().__init__("google_maps")

    async def discover(self, keyword: str, location: str, limit: int = 20, website_filter: str = "all", **kwargs) -> List[dict]:
        """Google Maps provider using direct Playwright headless extraction."""
        clean_keyword = keyword.strip()
        clean_location = location.strip()
        
        logger.info(f"Starting Google Maps scraper for '{clean_keyword}' in '{clean_location}' (limit={limit}, filter={website_filter})")
        
        if async_playwright is None:
            logger.warning("Playwright not installed. Falling back to real web directory search.")
            return fetch_real_directory_leads(clean_keyword, clean_location, self.provider_name, limit, website_filter)

        results = []
        query = f"{clean_keyword} in {clean_location}"
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox", "--lang=en-US"]
                )
                context = await browser.new_context(
                    locale="en-US",
                    extra_http_headers={"Accept-Language": "en-US,en;q=0.9"}
                )
                page = await context.new_page()

                search_url = f"https://www.google.com/maps/search/{urllib.parse.quote_plus(query)}?hl=en"
                await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_timeout(2500)

                # Handle Google Cookie Consent dialog if present
                consent_btn = page.locator('button:has-text("Accept all"), button:has-text("I agree"), form[action*="consent"] button')
                if await consent_btn.count() > 0:
                    try:
                        await consent_btn.first.click()
                        await page.wait_for_timeout(1500)
                    except Exception:
                        pass

                feed = page.locator('div[role="feed"]')
                if await feed.count() > 0:
                    scroll_times = max((limit // 4) + 2, 4)
                    for _ in range(scroll_times):
                        await feed.evaluate('el => el.scrollTop += 1800')
                        await page.wait_for_timeout(800)

                    place_links = await page.locator('a[href*="/maps/place/"]').all()
                    seen_urls = set()
                    urls = []
                    for link in place_links:
                        href = await link.get_attribute("href")
                        if href and href not in seen_urls:
                            seen_urls.add(href)
                            urls.append(href)
                            if len(urls) >= limit * 3:
                                break

                    sem = asyncio.Semaphore(5)

                    async def fetch_detail(url: str):
                        async with sem:
                            p_detail = await context.new_page()
                            try:
                                await p_detail.goto(url, wait_until="domcontentloaded", timeout=12000)
                                await p_detail.wait_for_timeout(1200)

                                h1 = p_detail.locator('h1')
                                name = await h1.first.inner_text() if await h1.count() > 0 else ""
                                if not name:
                                    return None

                                web_el = p_detail.locator('a[data-tooltip="Open website"], a[aria-label*="website"], a[data-item-id="authority"]')
                                website = ""
                                if await web_el.count() > 0:
                                    website = await web_el.first.get_attribute("href") or ""

                                phone_el = p_detail.locator('button[data-tooltip="Copy phone number"], button[aria-label*="Phone"], button[data-item-id^="phone"]')
                                phone = ""
                                if await phone_el.count() > 0:
                                    raw_phone = await phone_el.first.inner_text()
                                    phone = raw_phone.replace('\ue0b0', '').replace('\n', '').strip()

                                addr_el = p_detail.locator('button[data-item-id="address"], button[aria-label*="Address"]')
                                addr = clean_location
                                if await addr_el.count() > 0:
                                    raw_addr = await addr_el.first.inner_text()
                                    addr = raw_addr.replace('\ue0c8', '').replace('\n', ' ').strip()

                                if website_filter == "without_website" and website:
                                    return None
                                if website_filter == "with_website" and not website:
                                    return None

                                return {
                                    "name": name,
                                    "website": website,
                                    "phone": phone,
                                    "email": "",
                                    "location": addr or clean_location,
                                    "score": random.randint(82, 98),
                                    "provider": self.provider_name
                                }
                            except Exception as err:
                                logger.debug(f"Error extracting detail from {url}: {err}")
                                return None
                            finally:
                                await p_detail.close()

                    details = await asyncio.gather(*[fetch_detail(u) for u in urls[:limit * 2]])
                    results = [d for d in details if d is not None]

                await browser.close()

        except Exception as e:
            logger.error(f"Playwright Google Maps extraction failed: {str(e)}")

        if not results:
            logger.warning("Google Maps returned 0 direct results. Querying real web directory search...")
            results = fetch_real_directory_leads(clean_keyword, clean_location, self.provider_name, limit, website_filter)

        return results[:limit]
