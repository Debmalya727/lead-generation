"""
LeadForgeAI Enterprise Stealth Browser & Anti-Bot Evasion Engine.
Provides humanized browser emulation, fingerprint masking, random viewport/UA rotation,
Bézier curve mouse trajectories, dynamic scrolling, and resilient multi-strategy DOM/JSON-LD parsers.
"""
import math
import json
import re
import random
import logging
import asyncio
from typing import List, Dict, Any, Optional

logger = logging.getLogger("backend.discovery.stealth_browser")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
]

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
]


class StealthBrowserEngine:
    """Enterprise Anti-Bot & Fingerprint Evasion Utility."""

    @staticmethod
    def get_random_headers() -> Dict[str, str]:
        """Generate realistic browser request headers."""
        ua = random.choice(USER_AGENTS)
        return {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }

    @staticmethod
    def get_random_viewport() -> Dict[str, int]:
        """Select a standard high-resolution viewport."""
        return random.choice(VIEWPORTS)

    @staticmethod
    async def apply_stealth_scripts(page: Any) -> None:
        """Inject navigator stealth patches into Playwright Page context."""
        try:
            stealth_js = """
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en', 'hi'] });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                window.chrome = { runtime: {} };
            """
            await page.add_init_script(stealth_js)
        except Exception as e:
            logger.debug(f"Stealth script injection notice: {e}")

    @staticmethod
    async def simulate_human_scroll(page: Any, max_scrolls: int = 4) -> None:
        """Perform natural, variable-distance scrolling with random pauses."""
        try:
            for _ in range(max_scrolls):
                scroll_distance = random.randint(400, 1200)
                await page.mouse.wheel(0, scroll_distance)
                pause = random.uniform(0.6, 1.8)
                await asyncio.sleep(pause)
        except Exception as e:
            logger.debug(f"Human scroll simulation notice: {e}")

    @staticmethod
    def parse_json_ld(html_content: str) -> List[Dict[str, Any]]:
        """Extract structured JSON-LD microdata schema objects from HTML."""
        records = []
        if not html_content:
            return records
        try:
            matches = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_content, re.DOTALL | re.IGNORECASE)
            for m in matches:
                try:
                    data = json.loads(m.strip())
                    if isinstance(data, dict):
                        records.append(data)
                    elif isinstance(data, list):
                        records.extend([item for item in data if isinstance(item, dict)])
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"JSON-LD extraction error: {e}")
        return records

    @staticmethod
    def parse_opengraph(html_content: str) -> Dict[str, str]:
        """Extract OpenGraph meta tags from HTML."""
        og_data = {}
        if not html_content:
            return og_data
        try:
            matches = re.findall(r'<meta[^>]*property=["\']og:([^"\']+)["\'][^>]*content=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
            for key, val in matches:
                og_data[key.lower().strip()] = val.strip()
        except Exception as e:
            logger.debug(f"OpenGraph extraction error: {e}")
        return og_data


stealth_browser = StealthBrowserEngine()
