"""
Variables Engine for Outreach Campaign Personalization.

Replaces standard and custom placeholders in subject lines and email bodies:
- {{first_name}}
- {{company}}
- {{website}}
- {{industry}}
- {{pain_points}}
- {{buying_signal}}
- {{score}}
- {{city}}
- {{country}}
- {{unsubscribe_url}}
- Custom variables provided in recipient dictionary
"""
import re
from typing import Dict, Optional


class VariableEngine:
    """Engine for parsing and resolving variable template strings."""

    @staticmethod
    def extract_variables(text: str) -> list[str]:
        """Find all {{variable_name}} occurrences in text."""
        if not text:
            return []
        matches = re.findall(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", text)
        return list(set(matches))

    @staticmethod
    def render(
        template_str: str,
        variables: Dict[str, str],
        lead: Optional[object] = None,
        intel: Optional[object] = None,
        score_doc: Optional[object] = None,
    ) -> str:
        """
        Render a template string by replacing {{var}} placeholders
        using variables dict or extracting from Lead / Intelligence / Score objects.
        """
        if not template_str:
            return ""

        context: Dict[str, str] = {}

        # 1. Lead document defaults
        if lead:
            context["company"] = getattr(lead, "name", "") or ""
            context["website"] = getattr(lead, "website", "") or ""
            context["email"] = getattr(lead, "email", "") or ""

            loc = getattr(lead, "location", "") or ""
            if loc:
                parts = [p.strip() for p in loc.split(",")]
                context["city"] = parts[0]
                context["country"] = parts[-1] if len(parts) > 1 else "Global"
            else:
                context["city"] = "your city"
                context["country"] = "Global"

            # Derive first name from email or name
            name = getattr(lead, "name", "") or ""
            context["first_name"] = name.split()[0] if name else "There"

        # 2. Intelligence defaults
        if intel and hasattr(intel, "intelligence") and intel.intelligence:
            intel_data = intel.intelligence
            context["industry"] = getattr(intel_data, "industry", "") or "B2B"

            pps = getattr(intel_data, "pain_points", []) or []
            context["pain_points"] = pps[0] if pps else "scaling operations"

            bs = getattr(intel_data, "buying_signals", []) or []
            context["buying_signal"] = bs[0] if bs else "business expansion"

        # 3. Score document defaults
        if score_doc:
            sc = getattr(score_doc, "score", None)
            context["score"] = str(sc) if sc is not None else "85"

        # 4. Recipient custom variables override
        if variables:
            for k, v in variables.items():
                if v is not None:
                    context[k] = str(v)

        # 5. Replace placeholders
        def replace_match(match: re.Match) -> str:
            var_name = match.group(1).strip()
            return context.get(var_name, f"{{{{{var_name}}}}}")

        rendered = re.sub(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", replace_match, template_str)
        return rendered
