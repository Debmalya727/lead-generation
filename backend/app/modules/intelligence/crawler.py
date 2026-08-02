"""
Website Crawler using Playwright for full JavaScript rendering.

Extracts:
- Raw HTML content
- Visible text body
- Page title and meta description
- Technology stack signals (CMS, analytics, frameworks, hosting)
- Social media links
- Internal page links (contact, careers, about)
"""
import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

logger = logging.getLogger("backend.intelligence.crawler")


@dataclass
class CrawlResult:
    url: str
    title: str = ""
    meta_description: str = ""
    raw_html: str = ""
    text_content: str = ""
    tech_stack: List[Dict[str, str]] = field(default_factory=list)
    social_links: Dict[str, str] = field(default_factory=dict)
    contact_page: Optional[str] = None
    careers_page: Optional[str] = None
    about_page: Optional[str] = None
    error: Optional[str] = None
    success: bool = True


# Tech-stack signal detection patterns
TECH_SIGNALS = [
    # CMS
    {"pattern": r"wp-content|wp-includes|wordpress", "name": "WordPress", "category": "CMS"},
    {"pattern": r"shopify\.com|cdn\.shopify", "name": "Shopify", "category": "CMS"},
    {"pattern": r"wix\.com|wixstatic\.com", "name": "Wix", "category": "CMS"},
    {"pattern": r"squarespace\.com|static\.squarespace", "name": "Squarespace", "category": "CMS"},
    {"pattern": r"webflow\.io|webflow\.com", "name": "Webflow", "category": "CMS"},
    {"pattern": r"ghost\.io|ghost\.org", "name": "Ghost", "category": "CMS"},
    {"pattern": r"drupal\.js|drupal\.settings", "name": "Drupal", "category": "CMS"},
    {"pattern": r"joomla", "name": "Joomla", "category": "CMS"},
    # Analytics
    {"pattern": r"google-analytics\.com|gtag\(|googletagmanager", "name": "Google Analytics", "category": "Analytics"},
    {"pattern": r"mixpanel\.com", "name": "Mixpanel", "category": "Analytics"},
    {"pattern": r"segment\.com|segment\.io", "name": "Segment", "category": "Analytics"},
    {"pattern": r"hotjar\.com", "name": "Hotjar", "category": "Analytics"},
    {"pattern": r"clarity\.ms|ms\.clarity", "name": "Microsoft Clarity", "category": "Analytics"},
    {"pattern": r"intercom\.com|intercomcdn", "name": "Intercom", "category": "CRM/Support"},
    {"pattern": r"hubspot\.com|hs-scripts", "name": "HubSpot", "category": "CRM/Marketing"},
    {"pattern": r"salesforce\.com|force\.com", "name": "Salesforce", "category": "CRM"},
    # Frameworks/Libraries
    {"pattern": r"react[\./\-]|react\.development|__reactFiber", "name": "React", "category": "Framework"},
    {"pattern": r"angular[\./]|ng-version|ng-app", "name": "Angular", "category": "Framework"},
    {"pattern": r"vue[\./]|__vue__|vue\.runtime", "name": "Vue.js", "category": "Framework"},
    {"pattern": r"next\.js|__NEXT_DATA__", "name": "Next.js", "category": "Framework"},
    {"pattern": r"nuxt\.js|__nuxt__", "name": "Nuxt.js", "category": "Framework"},
    {"pattern": r"bootstrap\.min|bootstrap\.css|getbootstrap", "name": "Bootstrap", "category": "UI Library"},
    {"pattern": r"tailwindcss|tw-", "name": "Tailwind CSS", "category": "UI Library"},
    # CDN / Hosting signals
    {"pattern": r"cloudflare", "name": "Cloudflare", "category": "CDN"},
    {"pattern": r"amazonaws\.com|s3\.amazonaws", "name": "AWS", "category": "Hosting"},
    {"pattern": r"netlify\.app|netlify\.com", "name": "Netlify", "category": "Hosting"},
    {"pattern": r"vercel\.app|vercel\.com", "name": "Vercel", "category": "Hosting"},
    # E-commerce
    {"pattern": r"stripe\.com|stripe\.js", "name": "Stripe", "category": "Payments"},
    {"pattern": r"paypal\.com", "name": "PayPal", "category": "Payments"},
    {"pattern": r"woocommerce", "name": "WooCommerce", "category": "E-commerce"},
]

# Social media platform patterns
SOCIAL_PATTERNS = {
    "linkedin": r"linkedin\.com/(?:company|in)/",
    "twitter": r"(?:twitter|x)\.com/",
    "facebook": r"facebook\.com/",
    "instagram": r"instagram\.com/",
    "youtube": r"youtube\.com/(?:c/|channel/|@)",
    "github": r"github\.com/",
}


class WebsiteCrawler:
    """Playwright-based async website crawler with tech stack detection."""

    def __init__(self, timeout_ms: int = 20000):
        self.timeout_ms = timeout_ms

    async def crawl(self, url: str) -> CrawlResult:
        """
        Render and extract content from the given URL.
        Returns CrawlResult with success=False on error.
        """
        result = CrawlResult(url=url)

        try:
            result = await self._do_crawl(url, result)
        except Exception as e:
            error_msg = f"Crawler failed for {url}: {str(e)}"
            logger.error(error_msg)
            result.error = error_msg
            result.success = False

        return result

    async def _do_crawl(self, url: str, result: CrawlResult) -> CrawlResult:
        """Internal crawl implementation with Playwright."""
        from playwright.async_api import async_playwright

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-extensions",
                    "--disable-blink-features=AutomationControlled",
                ]
            )
            try:
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/122.0.0.0 Safari/537.36"
                    ),
                    extra_http_headers={
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                        "Sec-Ch-Ua-Mobile": "?0",
                        "Sec-Ch-Ua-Platform": '"Windows"',
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "none",
                        "Sec-Fetch-User": "?1",
                        "Upgrade-Insecure-Requests": "1",
                    },
                    ignore_https_errors=True,
                )
                page = await context.new_page()

                # Anti-bot stealth init script
                await page.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )

                # Block unnecessary media resources to speed up crawl
                await page.route(
                    "**/*.{png,jpg,jpeg,gif,webp,svg,ico,woff,woff2,ttf,eot}",
                    lambda r: r.abort()
                )

                logger.info(f"Crawling URL: {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)

                # Wait a moment for JS to settle
                await asyncio.sleep(2)

                raw_html = await page.content()
                result.raw_html = raw_html

                # Parse with BeautifulSoup
                soup = BeautifulSoup(raw_html, "lxml")

                # Extract title
                title_tag = soup.find("title")
                result.title = title_tag.get_text(strip=True) if title_tag else ""

                # Extract meta description
                meta_desc = soup.find("meta", attrs={"name": "description"})
                if meta_desc:
                    result.meta_description = meta_desc.get("content", "")

                # Extract clean text (remove scripts, styles, nav, footer)
                result.text_content = self._extract_text(soup)

                # Detect WAF / Anti-Bot block pages (e.g. Akamai 'Access Denied', Cloudflare 403)
                block_keywords = ["access denied", "403 forbidden", "cloudflare", "attention required", "robot or human", "captcha"]
                text_lower = result.text_content.lower()
                if len(result.text_content) < 300 or any(kw in text_lower for kw in block_keywords):
                    logger.warning(f"Anti-bot/WAF block detected for {url} (Title: '{result.title}'). Flagging for search engine fallback.")
                    result.success = False
                    result.error = f"Anti-bot WAF block on website ({result.title or 'Access Denied'})."
                else:
                    result.success = True

                # Detect tech stack
                result.tech_stack = self._detect_tech_stack(raw_html)

                # Extract social links and internal pages
                base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                all_links = self._extract_links(soup, base_url)
                result.social_links = self._find_social_links(all_links)
                result.contact_page = self._find_page(all_links, ["contact", "reach", "get-in-touch", "support"])
                result.careers_page = self._find_page(all_links, ["careers", "jobs", "work-with-us", "hiring", "join"])
                result.about_page = self._find_page(all_links, ["about", "team", "who-we-are", "our-story", "company"])

                logger.info(f"Crawl completed for {url}. Success={result.success}, Text length: {len(result.text_content)} chars")

            finally:
                await browser.close()

        return result

    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract visible text, removing scripts, styles, and boilerplate."""
        # Remove noise elements
        for tag in soup.find_all(["script", "style", "noscript", "iframe", "head"]):
            tag.decompose()

        # Get text content
        text = soup.get_text(separator="\n", strip=True)

        # Normalize whitespace: collapse multiple blank lines
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        cleaned = "\n".join(lines)

        # Cap at 15000 chars to avoid massive pages overloading the LLM
        return cleaned[:15000]

    def _detect_tech_stack(self, html: str) -> List[Dict[str, str]]:
        """Scan raw HTML against known tech signal patterns."""
        detected = {}
        html_lower = html.lower()

        for signal in TECH_SIGNALS:
            if re.search(signal["pattern"], html_lower, re.IGNORECASE):
                key = signal["name"]
                if key not in detected:
                    detected[key] = {"name": signal["name"], "category": signal["category"]}

        return list(detected.values())

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all internal and external <a> hrefs from the page."""
        links = set()
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if not href or href.startswith("#"):
                continue
            if href.startswith(("http://", "https://")):
                links.add(href)
            elif href.startswith("/"):
                links.add(urljoin(base_url, href))
        return list(links)

    def _find_social_links(self, links: List[str]) -> Dict[str, str]:
        """Match extracted links against known social media URL patterns."""
        socials = {}
        for link in links:
            for platform, pattern in SOCIAL_PATTERNS.items():
                if platform not in socials and re.search(pattern, link, re.IGNORECASE):
                    socials[platform] = link
                    break
        return socials

    def _find_page(self, links: List[str], keywords: List[str]) -> Optional[str]:
        """Find the first link whose path contains any of the given keywords."""
        for link in links:
            path = urlparse(link).path.lower()
            for kw in keywords:
                if kw in path:
                    return link
        return None
