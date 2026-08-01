import re
import random
import logging
import urllib.parse
from typing import List

logger = logging.getLogger(__name__)

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None

try:
    import httpx
    from bs4 import BeautifulSoup
except ImportError:
    httpx = None
    BeautifulSoup = None


def fetch_real_directory_leads(
    keyword: str,
    location: str,
    provider_name: str,
    limit: int = 20,
    website_filter: str = "all"
) -> List[dict]:
    """Fetch real business leads from web search & business directory networks."""
    clean_keyword = keyword.strip()
    clean_location = location.strip()

    site_map = {
        "justdial": "justdial.com",
        "indiamart": "indiamart.com",
        "tradeindia": "tradeindia.com"
    }

    domain = site_map.get(provider_name.lower())
    if domain:
        query = f'"{clean_keyword}" "{clean_location}" site:{domain}'
    else:
        query = f'"{clean_keyword}" in "{clean_location}" business contact phone website'

    results = []
    seen_names = set()

    # 1. Try DDGS library if available
    if DDGS is not None:
        try:
            with DDGS() as ddgs:
                raw_items = list(ddgs.text(query, max_results=max(limit * 3, 30)))
                for item in raw_items:
                    title = item.get("title", "").strip()
                    snippet = item.get("body", "").strip()
                    href = item.get("href", "").strip()
                    _process_and_add_lead(title, snippet, href, clean_location, provider_name, website_filter, results, seen_names, limit)
                    if len(results) >= limit:
                        return results
        except Exception as e:
            logger.warning(f"DDGS search failed: {e}. Trying httpx fallback...")

    # 2. Fallback to direct httpx request to DuckDuckGo HTML if DDGS fails or returns 0
    if len(results) < limit and httpx is not None and BeautifulSoup is not None:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9"
            }
            client = httpx.Client(headers=headers, timeout=12.0, follow_redirects=True)
            resp = client.post("https://html.duckduckgo.com/html/", data={"q": query})
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                res_divs = soup.select(".result")
                for div in res_divs:
                    a_tag = div.select_one(".result__title a")
                    snippet_tag = div.select_one(".result__snippet")
                    if not a_tag:
                        continue
                    title = a_tag.get_text(strip=True)
                    href = a_tag.get("href", "").strip()
                    snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

                    if "uddg=" in href:
                        match = re.search(r'uddg=([^&]+)', href)
                        if match:
                            href = urllib.parse.unquote(match.group(1))

                    _process_and_add_lead(title, snippet, href, clean_location, provider_name, website_filter, results, seen_names, limit)
                    if len(results) >= limit:
                        break
        except Exception as e:
            logger.error(f"HTTPX DuckDuckGo extraction failed: {e}")

    return results[:limit]


def _process_and_add_lead(title, snippet, href, clean_location, provider_name, website_filter, results, seen_names, limit):
    if not title or len(title) < 3:
        return

    clean_name = re.sub(
        r'\s*[-|:|–]\s*(Justdial|IndiaMART|TradeIndia|Official Site|Home|Contact Us|Phone Number|Price|Cost|Reviews).*$',
        '', title, flags=re.IGNORECASE
    ).strip()

    clean_name = re.sub(
        r'^(Buy|Find|Top\s+\d+|Best\ |List of\ |Suppliers of\ |Manufacturers of\ |Wholesale\ )',
        '', clean_name, flags=re.IGNORECASE
    ).strip()

    if not clean_name or len(clean_name) < 3:
        return

    name_key = clean_name.lower()
    if name_key in seen_names:
        return
    seen_names.add(name_key)

    phone = ""
    phone_match = re.search(r'(\+?\d{1,4}[-.\s]?)?\(?\d{2,5}\)?[-.\s]?\d{3,5}[-.\s]?\d{3,5}', snippet)
    if phone_match and len(phone_match.group(0).strip()) >= 7:
        phone = phone_match.group(0).strip()

    email = ""
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', snippet)
    if email_match:
        email = email_match.group(0).strip()

    website = ""
    if href and not any(x in href.lower() for x in ['facebook.com', 'instagram.com', 'wikipedia.org', 'youtube.com', 'twitter.com', 'duckduckgo.com']):
        website = href

    if website_filter == "without_website" and website:
        website = ""
    elif website_filter == "with_website" and not website:
        return

    score = 72
    if website:
        score += 15
    if phone:
        score += 10
    if email:
        score += 5

    results.append({
        "name": clean_name,
        "website": website,
        "phone": phone,
        "email": email,
        "location": clean_location,
        "score": min(score, 98),
        "provider": provider_name
    })
