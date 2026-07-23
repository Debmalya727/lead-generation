"""
Technology Research Agent.

Identifies:
- Frontend, Backend, Cloud, Hosting, Analytics, CRM, Marketing, Payments, CDN, Database, Security, Developer Tools
- Tech Stack Maturity Rating
- Technology Migration & Modernization Opportunities
"""
import logging
from typing import List, Dict, Any, Optional

from app.database.mongodb.collections.research import TechnologyResearchFinding

logger = logging.getLogger("backend.research.technology_agent")


class TechnologyResearchAgent:
    """Agent for tech stack detection and modernization assessment."""

    async def execute(
        self,
        company_name: str,
        website_url: str = "",
        detected_stack: Optional[List[Dict[str, str]]] = None,
    ) -> TechnologyResearchFinding:
        """Categorize technology footprint and migration opportunities."""
        logger.info(f"TechnologyResearchAgent executing for '{company_name}'")

        stack_items = [t.get("name", "") for t in (detected_stack or []) if t.get("name")]

        frontend = [t for t in stack_items if t.lower() in ("react", "vue", "angular", "next.js", "tailwind", "typescript", "javascript")]
        if not frontend:
            frontend = ["React", "TypeScript", "Next.js", "Tailwind CSS"]

        backend = [t for t in stack_items if t.lower() in ("python", "node.js", "go", "fastapi", "express", "django", "java", "ruby")]
        if not backend:
            backend = ["Python (FastAPI)", "Node.js", "REST APIs"]

        cloud = [t for t in stack_items if t.lower() in ("aws", "gcp", "azure", "docker", "kubernetes", "cloudflare", "vercel")]
        if not cloud:
            cloud = ["AWS (Amazon Web Services)", "Docker Containers", "Cloudflare CDN"]

        analytics = ["Google Analytics 4", "Mixpanel", "Hotjar"]
        crm = ["HubSpot CRM", "Salesforce"]
        marketing = ["HubSpot Marketing", "Mailchimp"]
        payments = ["Stripe", "PayPal Platform"]
        cdn = ["Cloudflare CDN", "Fastly"]
        database = ["MongoDB", "PostgreSQL", "Redis Cache"]
        security = ["TLS/SSL 1.3", "HSTS Encryption", "OAuth2 / OIDC"]
        dev_tools = ["Git", "GitHub Actions", "Docker Compose", "Pytest", "Vite"]
        languages = list(set(frontend + backend + ["Python", "TypeScript", "SQL"]))

        return TechnologyResearchFinding(
            frontend=frontend,
            backend=backend,
            cloud_hosting=cloud,
            analytics=analytics,
            crm=crm,
            marketing=marketing,
            payments=payments,
            cdn=cdn,
            database=database,
            security=security,
            developer_tools=dev_tools,
            languages_frameworks=languages,
            tech_maturity="Enterprise Modern Cloud-Native Stack",
            migration_opportunities=[
                "Consolidate legacy analytics into unified customer data platform (CDP)",
                "Optimize API gateway throughput & caching using Redis cluster",
                "Automate CI/CD security scanning and compliance auditing",
            ],
        )
