"""
Enterprise Lead Normalization Engine.
Cleanses, formats, and standardizes raw lead data from heterogeneous providers
into unified canonical NormalizedLead instances.
"""
import re
import urllib.parse
from typing import Dict, Any, List, Optional
from app.modules.discovery.normalization.models import NormalizedLead


class LeadNormalizer:
    """Standardizes heterogeneous provider output into clean, canonical records."""

    @staticmethod
    def normalize_company_name(name: str) -> str:
        """Clean and normalize business name."""
        if not name:
            return ""
        
        # Remove extra whitespace and newlines
        clean = " ".join(name.strip().split())
        
        # Capitalize nicely if all uppercase or all lowercase
        if clean.isupper() or clean.islower():
            clean = clean.title()

        return clean

    @staticmethod
    def extract_domain(url: str) -> Optional[str]:
        """Extract canonical domain from website URL (e.g., 'https://www.acme.com/about' -> 'acme.com')."""
        if not url:
            return None
        
        url_str = url.strip().lower()
        if not url_str.startswith(("http://", "https://")):
            url_str = "http://" + url_str
            
        try:
            parsed = urllib.parse.urlparse(url_str)
            domain = parsed.netloc or parsed.path
            # Strip port if present
            domain = domain.split(":")[0]
            # Strip leading 'www.'
            if domain.startswith("www."):
                domain = domain[4:]
            return domain if len(domain) > 3 and "." in domain else None
        except Exception:
            return None

    @staticmethod
    def normalize_website(url: str) -> Optional[str]:
        """Ensure website has proper protocol scheme."""
        if not url:
            return None
        url_str = url.strip()
        if not url_str:
            return None
        if not url_str.startswith(("http://", "https://")):
            return f"https://{url_str}"
        return url_str

    @staticmethod
    def normalize_phone(phone: str, default_country: str = "IN") -> Optional[str]:
        """
        Normalize raw phone string to clean format.
        Handles Indian numbers (+91), US numbers (+1), and general international formats.
        """
        if not phone:
            return None
        
        # Extract digits and '+' sign
        cleaned_digits = re.sub(r"[^\d+]", "", phone.strip())
        digits_only = re.sub(r"[^\d]", "", cleaned_digits)

        if not digits_only or len(digits_only) < 7:
            return None

        if default_country == "IN":
            # Handle Indian mobile/landline numbers (10 digits, or 11/12 with leading 0/91)
            if len(digits_only) == 10:
                return f"+91{digits_only}"
            elif len(digits_only) == 11 and digits_only.startswith("0"):
                return f"+91{digits_only[1:]}"
            elif len(digits_only) == 12 and digits_only.startswith("91"):
                return f"+91{digits_only[2:]}"
        elif default_country == "US":
            if len(digits_only) == 10:
                return f"+1{digits_only}"
            elif len(digits_only) == 11 and digits_only.startswith("1"):
                return f"+1{digits_only[1:]}"

        if cleaned_digits.startswith("+"):
            return f"+{digits_only}"
        return f"+{digits_only}"

    @staticmethod
    def normalize_gst(gst: str) -> Optional[str]:
        """Validate and format Indian GSTIN (15 alphanumeric characters)."""
        if not gst:
            return None
        clean_gst = re.sub(r"[^A-Za-z0-9]", "", gst.upper().strip())
        # GST pattern: 2 digits (state code), 10 char PAN, 1 entity code, 1 Z, 1 checksum digit
        if len(clean_gst) == 15 and re.match(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$", clean_gst):
            return clean_gst
        return clean_gst if len(clean_gst) == 15 else None

    @staticmethod
    def generate_fingerprint(company_name: str, domain: Optional[str] = None, phone: Optional[str] = None) -> str:
        """
        Generate canonical deduplication fingerprint string.
        Combines normalized name + domain or phone.
        """
        name_key = re.sub(r"[^a-z0-9]", "", company_name.lower().strip())
        domain_key = domain.lower().strip() if domain else ""
        phone_key = re.sub(r"[^\d]", "", phone) if phone else ""

        # Priority 1: Name + Domain
        if domain_key:
            return f"fp_dom_{name_key}_{domain_key}"
        # Priority 2: Name + Phone
        if phone_key:
            return f"fp_ph_{name_key}_{phone_key[-10:]}"
        # Fallback: Name only
        return f"fp_nm_{name_key}"

    @classmethod
    def normalize_raw_lead(cls, raw: Any, provider_name: str) -> NormalizedLead:
        """
        Convert a raw provider dictionary into a clean NormalizedLead model.
        """
        if isinstance(raw, NormalizedLead):
            return raw

        if not isinstance(raw, dict):
            if hasattr(raw, "__dict__"):
                raw = raw.__dict__
            else:
                raw = {"name": str(raw)}

        company_name = cls.normalize_company_name(
            raw.get("name") or raw.get("company_name") or raw.get("title") or ""
        )
        
        raw_website = raw.get("website") or raw.get("url") or ""
        website = cls.normalize_website(raw_website)
        domain = cls.extract_domain(raw_website)

        raw_phones = raw.get("phones") or ([raw.get("phone")] if raw.get("phone") else [])
        phones = []
        for p in raw_phones:
            if p:
                norm_p = cls.normalize_phone(str(p))
                if norm_p and norm_p not in phones:
                    phones.append(norm_p)

        raw_emails = raw.get("emails") or ([raw.get("email")] if raw.get("email") else [])
        emails = [e.lower().strip() for e in raw_emails if e and "@" in e]

        raw_categories = raw.get("categories") or ([raw.get("category")] if raw.get("category") else [])
        categories = [c.strip() for c in raw_categories if c]

        gst = cls.normalize_gst(raw.get("gst") or "")
        fingerprint = cls.generate_fingerprint(company_name, domain, phones[0] if phones else None)

        coords = raw.get("coordinates")
        if not coords and "latitude" in raw and "longitude" in raw:
            try:
                coords = {"lat": float(raw["latitude"]), "lng": float(raw["longitude"])}
            except Exception:
                coords = None

        return NormalizedLead(
            provider_name=provider_name,
            provider_id=raw.get("provider_id") or raw.get("id"),
            raw_data=raw,
            company_name=company_name,
            trade_name=raw.get("trade_name"),
            phones=phones,
            emails=emails,
            website=website,
            website_domain=domain,
            address=raw.get("address"),
            city=raw.get("city") or raw.get("location"),
            state=raw.get("state"),
            postal_code=raw.get("postal_code") or raw.get("zipcode"),
            country=raw.get("country", "IN"),
            coordinates=coords,
            gst=gst,
            categories=categories,
            industry=raw.get("industry"),
            products=raw.get("products", []),
            business_type=raw.get("business_type"),
            rating=float(raw["rating"]) if raw.get("rating") is not None else None,
            review_count=int(raw["review_count"]) if raw.get("review_count") is not None else None,
            photos=raw.get("photos", []),
            business_status=raw.get("business_status", "OPERATIONAL"),
            description=raw.get("description"),
            initial_score=int(raw.get("score", 50)),
            fingerprint=fingerprint,
        )


lead_normalizer = LeadNormalizer()
