"""
Utility for identifying directory, aggregator, and social platform domains
to prevent crawling generic portal structures (e.g. Justdial, IndiaMART, TradeIndia).
"""
import re
from typing import Optional
from urllib.parse import urlparse

DIRECTORY_DOMAINS = {
    "justdial.com",
    "tradeindia.com",
    "indiamart.com",
    "yellowpages.com",
    "yellowpages.in",
    "sulekha.com",
    "yelp.com",
    "tripadvisor.com",
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "twitter.com",
    "x.com",
    "youtube.com",
    "business.google.com",
    "google.com",
    "mapquest.com",
    "trustpilot.com",
    "glassdoor.com",
    "indeed.com",
    "crunchbase.com",
    "exportersindia.com",
}


def is_directory_domain(url_or_domain: Optional[str]) -> bool:
    """Check if a URL or domain belongs to a business directory or social platform."""
    if not url_or_domain:
        return False

    clean = url_or_domain.strip().lower()
    if "://" in clean:
        netloc = urlparse(clean).netloc
    else:
        netloc = clean.split("/")[0]

    netloc = re.sub(r"^www\.", "", netloc)

    for domain in DIRECTORY_DOMAINS:
        if netloc == domain or netloc.endswith("." + domain):
            return True

    return False
