"""
EntityExtractor for Phase 12: Enterprise Conversational CRM.

Extracts structured business entities from natural language inputs.
"""
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("backend.conversation.intent.entity_extractor")


class EntityExtractor:
    """Extractor parsing B2B entities from text inputs."""

    KNOWN_COMPANIES = ["acme", "tesla", "microsoft", "google", "apple", "amazon", "meta", "nvidia", "salesforce", "hubspot", "snowflake", "databricks"]

    def extract(self, text: str, context_memory: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Extract structured entities.
        Returns dictionary of extracted fields.
        """
        entities: Dict[str, Any] = {}
        cleaned = text.strip()

        # 1. Company Name extraction
        company_name = self._extract_company(cleaned)
        if company_name:
            entities["company_name"] = company_name
        elif context_memory and context_memory.get("current_company"):
            entities["company_name"] = context_memory["current_company"]

        # 2. Industry extraction
        for ind in ["saas", "software", "healthcare", "fintech", "e-commerce", "retail", "manufacturing", "ai", "cybersecurity"]:
            if re.search(r"\b" + ind + r"\b", cleaned, re.IGNORECASE):
                entities["industry"] = ind.upper() if ind in ["saas", "ai"] else ind.title()
                break

        # 3. Country / Region extraction
        for country in ["united states", "united kingdom", "usa", "us", "uk", "india", "germany", "singapore", "canada"]:
            if re.search(r"\b" + country + r"\b", cleaned, re.IGNORECASE):
                c_lower = country.lower()
                entities["country"] = "USA" if c_lower in ["us", "usa", "united states"] else ("UK" if c_lower in ["uk", "united kingdom"] else country.title())
                break

        # 4. Employee Range extraction (e.g. 50-200, 100-500 employees)
        emp_match = re.search(r"(\d+[\s\-]*(?:to|-)?\s*\d+)\s*(?:employees|people|staff)?", cleaned, re.IGNORECASE)
        if emp_match:
            entities["employee_range"] = emp_match.group(1).replace(" ", "")

        # 5. Email extraction
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", cleaned)
        if email_match:
            entities["email"] = email_match.group(0)

        # 6. Workflow Name extraction
        for wf in ["sales_discovery", "lead_qualification", "sales_intelligence", "company_research", "outreach_campaign", "executive_report_gen"]:
            if wf in cleaned.lower() or wf.replace("_", " ") in cleaned.lower():
                entities["workflow_name"] = wf
                break

        # 7. Report Type extraction
        for rtype in ["executive", "sales", "research", "qualification", "pdf", "csv"]:
            if rtype in cleaned.lower():
                entities["report_type"] = rtype
                break

        return entities

    def _extract_company(self, text: str) -> Optional[str]:
        """Extract target company name from input string."""
        # Check slash command e.g. "/research Acme Corp"
        if text.startswith("/"):
            parts = text.split(maxsplit=1)
            if len(parts) > 1:
                return parts[1].strip().title()

        # Check explicit keywords e.g. "research Tesla", "for Microsoft"
        match = re.search(r"(?:for|research|about|investigate|company|target|check|score)\s+([A-Za-z0-9\-\.]{2,30})", text, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            if candidate.lower() not in ["the", "a", "an", "for", "in", "with"]:
                return candidate.title()

        # Check known company list
        for kc in self.KNOWN_COMPANIES:
            if re.search(r"\b" + kc + r"\b", text, re.IGNORECASE):
                return kc.title()

        return None
