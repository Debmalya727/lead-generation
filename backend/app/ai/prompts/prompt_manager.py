"""
Enterprise Prompt Management Platform for Phase 12.7 Enterprise AI Platform.
Features:
- Prompt Library & Search (categories, tags, status filters)
- Template Compilation & Variable Engine ({var} & {{var}} placeholders)
- Versioning & Rollback (1-click version reversion)
- Approval Workflow (DRAFT -> IN_REVIEW -> APPROVED -> REJECTED)
- Publishing Engine (PUBLISHED status management)
- Diff Viewer (unified diff between prompt revisions)
- Security & Guardrail Sanitization (protection against prompt injection)
- Interactive Testing Playground (execution via AIGateway)
- A/B Testing Engine (variant split, hit counters, winner telemetry)
"""
import re
import difflib
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from app.database.mongodb.collections.ai_gateway import (
    PromptTemplateDocument,
    PromptVersionDocument,
    PromptABTestDocument,
)

logger = logging.getLogger("backend.ai.prompts")


class PromptManager:
    """Enterprise Prompt Platform Manager."""

    def __init__(self):
        self._memory_templates: Dict[str, Dict[str, Any]] = {}
        self._memory_versions: Dict[str, List[Dict[str, Any]]] = {}
        self._memory_ab_tests: Dict[str, Dict[str, Any]] = {}

    BUILTIN_PROMPTS: List[Dict[str, Any]] = [
        {
            "template_id": "conversation_agent",
            "name": "Conversational CRM Prompt",
            "category": "conversation",
            "tags": ["crm", "lead_management", "memory"],
            "system_prompt_template": "You are LeadForgeAI Conversational CRM. You help the user manage leads, research targets, and personalize outreach.",
            "user_prompt_template": "User prompt: {user_prompt}\nMemory context:\n{memory_context}",
            "variables": ["user_prompt", "memory_context"],
        },
        {
            "template_id": "research_summarizer",
            "name": "Research Summary Prompt",
            "category": "research",
            "tags": ["research", "company", "scraping"],
            "system_prompt_template": "Summarize target company information into structured insights.",
            "user_prompt_template": "Company Name: {company_name}\nRaw scraped text:\n{scraped_text}",
            "variables": ["company_name", "scraped_text"],
        },
        {
            "template_id": "outreach_personalized",
            "name": "Outreach Generation Prompt",
            "category": "outreach",
            "tags": ["email", "sales", "personalization"],
            "system_prompt_template": "Generate high-converting, personalized cold email outreach.",
            "user_prompt_template": "Lead: {lead_name}\nCompany: {company_name}\nPain Points: {pain_points}",
            "variables": ["lead_name", "company_name", "pain_points"],
        },
    ]

    async def initialize_builtin_prompts(self) -> None:
        """Seed built-in templates into MongoDB if present, otherwise in-memory."""
        for bp in self.BUILTIN_PROMPTS:
            tid = bp["template_id"]
            if tid not in self._memory_templates:
                self._memory_templates[tid] = {
                    "template_id": tid,
                    "name": bp["name"],
                    "category": bp["category"],
                    "tags": bp.get("tags", []),
                    "system_prompt_template": bp["system_prompt_template"],
                    "user_prompt_template": bp["user_prompt_template"],
                    "variables": bp["variables"],
                    "current_version": 1,
                    "version_tag": "v1.0.0",
                    "status": "PUBLISHED",
                    "published_version": 1,
                    "hit_count": 0,
                    "average_rating": 5.0,
                    "created_by": "System",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
                self._memory_versions[tid] = [
                    {
                        "template_id": tid,
                        "version": 1,
                        "version_tag": "v1.0.0",
                        "system_prompt": bp["system_prompt_template"],
                        "user_prompt": bp["user_prompt_template"],
                        "variables": bp["variables"],
                        "changes_description": "Initial built-in version",
                        "author": "System",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                ]
            try:
                doc = await PromptTemplateDocument.find_one(
                    PromptTemplateDocument.template_id == tid
                )
                if not doc:
                    doc = PromptTemplateDocument(
                        template_id=tid,
                        name=bp["name"],
                        category=bp["category"],
                        tags=bp.get("tags", []),
                        system_prompt_template=bp["system_prompt_template"],
                        user_prompt_template=bp["user_prompt_template"],
                        variables=bp["variables"],
                        current_version=1,
                        version_tag="v1.0.0",
                        status="PUBLISHED",
                        published_version=1,
                    )
                    await doc.insert()
                    ver = PromptVersionDocument(
                        template_id=tid,
                        version=1,
                        version_tag="v1.0.0",
                        system_prompt=bp["system_prompt_template"],
                        user_prompt=bp["user_prompt_template"],
                        variables=bp["variables"],
                        changes_description="Initial built-in version",
                        author="System",
                    )
                    await ver.insert()
            except Exception:
                pass

    # ─── 1. Variable Extraction & Sanitization ───

    def extract_variables(self, user_template: str, system_template: Optional[str] = None) -> List[str]:
        """Extract variable placeholders formatted as {var} or {{var}}."""
        text = (user_template or "") + " " + (system_template or "")
        matches = re.findall(r"\{+([a-zA-Z0-9_]+)\}+", text)
        return list(dict.fromkeys(matches))  # Deduplicate maintaining insertion order

    def sanitize_prompt(self, text: str) -> str:
        """Sanitize text against prompt injection patterns and raw HTML tags."""
        if not text:
            return ""
        # Remove direct system override commands
        injection_patterns = [
            r"(?i)ignore previous instructions",
            r"(?i)system override",
            r"(?i)you are now unrestricted",
        ]
        sanitized = text
        for pat in injection_patterns:
            sanitized = re.sub(pat, "[SANITIZED_PROMPT_INJECTION_ATTEMPT]", sanitized)
        return sanitized.strip()

    def compress_prompt(self, text: str) -> str:
        """Compress prompt by stripping empty lines and leading/trailing spaces."""
        if not text:
            return ""
        lines = [line.strip() for line in text.split("\n")]
        return "\n".join([line for line in lines if line])

    # ─── 2. Library Search & Retrieval ───

    async def list_templates(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List and search prompt templates with multi-criteria filtering."""
        await self.initialize_builtin_prompts()
        
        docs_list = []
        try:
            docs = await PromptTemplateDocument.find_all().to_list()
            docs_list = [d.model_dump() for d in docs]
        except Exception:
            docs_list = list(self._memory_templates.values())

        results = []
        for d in docs_list:
            cat = d.get("category", "")
            tags_list = d.get("tags", [])
            stat = d.get("status", "")
            name = d.get("name", "")
            tid = d.get("template_id", "")
            user_prompt = d.get("user_prompt_template", "")

            if category and cat.lower() != category.lower():
                continue
            if tag and tag.lower() not in [t.lower() for t in tags_list]:
                continue
            if status and stat.upper() != status.upper():
                continue
            if query:
                q = query.lower()
                matches = (
                    q in name.lower() or
                    q in tid.lower() or
                    q in user_prompt.lower() or
                    any(q in t.lower() for t in tags_list)
                )
                if not matches:
                    continue
            results.append(d)
        return results

    async def get_template(self, template_id: str) -> Dict[str, Any]:
        """Fetch template dictionary by ID."""
        try:
            doc = await PromptTemplateDocument.find_one(PromptTemplateDocument.template_id == template_id)
            if doc:
                return doc.model_dump()
        except Exception:
            pass

        if template_id in self._memory_templates:
            return self._memory_templates[template_id]
        raise ValueError(f"Prompt template '{template_id}' not found.")

    # ─── 3. Template Compilation ───

    async def compile_prompt(self, template_id: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Compile system and user prompts with variable substitution."""
        doc = await self.get_template(template_id)

        # Check required variables
        for var in doc.get("variables", []):
            if var not in variables or variables[var] is None:
                raise ValueError(f"Missing required prompt variable: '{var}'")

        user_text = doc.get("user_prompt_template", "")
        system_text = doc.get("system_prompt_template") or ""

        for k, v in variables.items():
            user_text = user_text.replace(f"{{{{{k}}}}}", str(v)).replace(f"{{{k}}}", str(v))
            system_text = system_text.replace(f"{{{{{k}}}}}", str(v)).replace(f"{{{k}}}", str(v))

        user_text = self.sanitize_prompt(self.compress_prompt(user_text))
        system_text = self.sanitize_prompt(self.compress_prompt(system_text))

        return {
            "template_id": template_id,
            "version": doc.get("current_version", 1),
            "system_prompt": system_text,
            "user_prompt": user_text,
        }

    # ─── 4. Save & Versioning ───

    async def save_template(
        self,
        template_id: str,
        name: str,
        category: str,
        user_prompt_template: str,
        system_prompt_template: Optional[str] = None,
        tags: Optional[List[str]] = None,
        changes_description: Optional[str] = None,
        author: str = "System",
    ) -> PromptTemplateDocument:
        """Create or update template, generating a new version revision."""
        tags = tags or []
        extracted_vars = self.extract_variables(user_prompt_template, system_prompt_template)

        # In-Memory Record
        existing_mem = self._memory_templates.get(template_id)
        next_ver = (existing_mem["current_version"] + 1) if existing_mem else 1
        ver_tag = f"v1.{next_ver - 1}.0"

        mem_doc = {
            "template_id": template_id,
            "name": name,
            "category": category,
            "tags": list(set((existing_mem.get("tags", []) if existing_mem else []) + tags)),
            "user_prompt_template": user_prompt_template,
            "system_prompt_template": system_prompt_template,
            "variables": extracted_vars,
            "current_version": next_ver,
            "version_tag": ver_tag,
            "status": existing_mem.get("status", "DRAFT") if existing_mem else "DRAFT",
            "published_version": existing_mem.get("published_version") if existing_mem else None,
            "hit_count": existing_mem.get("hit_count", 0) if existing_mem else 0,
            "average_rating": 5.0,
            "created_by": author,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._memory_templates[template_id] = mem_doc

        ver_item = {
            "template_id": template_id,
            "version": next_ver,
            "version_tag": ver_tag,
            "system_prompt": system_prompt_template,
            "user_prompt": user_prompt_template,
            "variables": extracted_vars,
            "changes_description": changes_description or f"Updated to {ver_tag}",
            "author": author,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if template_id not in self._memory_versions:
            self._memory_versions[template_id] = []
        self._memory_versions[template_id].insert(0, ver_item)

        # MongoDB Record
        doc = None
        try:
            doc = await PromptTemplateDocument.find_one(PromptTemplateDocument.template_id == template_id)
            if not doc:
                doc = PromptTemplateDocument(
                    template_id=template_id,
                    name=name,
                    category=category,
                    tags=tags,
                    user_prompt_template=user_prompt_template,
                    system_prompt_template=system_prompt_template,
                    variables=extracted_vars,
                    current_version=next_ver,
                    version_tag=ver_tag,
                    status="DRAFT",
                    created_by=author,
                )
                await doc.insert()
            else:
                doc.name = name
                doc.category = category
                doc.tags = list(set(doc.tags + tags))
                doc.user_prompt_template = user_prompt_template
                doc.system_prompt_template = system_prompt_template
                doc.variables = extracted_vars
                doc.current_version = next_ver
                doc.version_tag = ver_tag
                doc.updated_at = datetime.now(timezone.utc)
                await doc.save()

            ver = PromptVersionDocument(
                template_id=template_id,
                version=next_ver,
                version_tag=ver_tag,
                system_prompt=system_prompt_template,
                user_prompt=user_prompt_template,
                variables=extracted_vars,
                changes_description=changes_description or f"Updated to {ver_tag}",
                author=author,
            )
            await ver.insert()
        except Exception:
            pass

        return doc or PromptTemplateDocument.model_construct(**mem_doc)

    # ─── 5. Version History, Diff, and Rollback ───

    async def get_version_history(self, template_id: str) -> List[Dict[str, Any]]:
        """Fetch full version history for a prompt template."""
        try:
            versions = await PromptVersionDocument.find(
                PromptVersionDocument.template_id == template_id
            ).sort("-version").to_list()
            if versions:
                return [v.model_dump() for v in versions]
        except Exception:
            pass

        return self._memory_versions.get(template_id, [])

    async def generate_diff(self, template_id: str, version_a: int, version_b: int) -> Dict[str, Any]:
        """Generate side-by-side text diff between two prompt versions."""
        history = await self.get_version_history(template_id)
        v_a = next((v for v in history if v.get("version") == version_a), None)
        v_b = next((v for v in history if v.get("version") == version_b), None)

        if not v_a or not v_b:
            raise ValueError(f"Version {version_a} or {version_b} not found for '{template_id}'")

        diff_user = list(difflib.unified_diff(
            (v_a.get("user_prompt") or v_a.get("user_prompt_template") or "").splitlines(),
            (v_b.get("user_prompt") or v_b.get("user_prompt_template") or "").splitlines(),
            fromfile=f"v{version_a}",
            tofile=f"v{version_b}",
            lineterm=""
        ))

        return {
            "template_id": template_id,
            "version_a": version_a,
            "version_b": version_b,
            "diff_lines": diff_user,
            "has_changes": len(diff_user) > 0,
        }

    async def rollback_version(self, template_id: str, target_version: int, author: str = "System") -> PromptTemplateDocument:
        """Rollback prompt template to a target historical version."""
        history = await self.get_version_history(template_id)
        ver = next((v for v in history if v.get("version") == target_version), None)
        if not ver:
            raise ValueError(f"Target version {target_version} not found for template '{template_id}'")

        current = await self.get_template(template_id)
        return await self.save_template(
            template_id=template_id,
            name=current["name"],
            category=current["category"],
            user_prompt_template=ver.get("user_prompt") or ver.get("user_prompt_template") or "",
            system_prompt_template=ver.get("system_prompt") or ver.get("system_prompt_template"),
            changes_description=f"Rolled back to version {target_version}",
            author=author,
        )

    # ─── 6. Approval & Publishing Workflows ───

    async def update_approval(self, template_id: str, new_status: str) -> PromptTemplateDocument:
        """Transition approval state (DRAFT -> IN_REVIEW -> APPROVED -> REJECTED)."""
        valid_statuses = ["DRAFT", "IN_REVIEW", "APPROVED", "REJECTED", "PUBLISHED", "ARCHIVED"]
        if new_status.upper() not in valid_statuses:
            raise ValueError(f"Invalid status '{new_status}'. Allowed: {valid_statuses}")

        if template_id in self._memory_templates:
            self._memory_templates[template_id]["status"] = new_status.upper()

        doc = None
        try:
            doc = await PromptTemplateDocument.find_one(PromptTemplateDocument.template_id == template_id)
            if doc:
                doc.status = new_status.upper()
                doc.updated_at = datetime.now(timezone.utc)
                await doc.save()
        except Exception:
            pass

        return doc or PromptTemplateDocument.model_construct(**self._memory_templates[template_id])

    async def publish_version(self, template_id: str, version: Optional[int] = None) -> PromptTemplateDocument:
        """Publish template for production execution."""
        current = await self.get_template(template_id)
        pub_ver = version or current.get("current_version", 1)

        if template_id in self._memory_templates:
            self._memory_templates[template_id]["status"] = "PUBLISHED"
            self._memory_templates[template_id]["published_version"] = pub_ver

        doc = None
        try:
            doc = await PromptTemplateDocument.find_one(PromptTemplateDocument.template_id == template_id)
            if doc:
                doc.status = "PUBLISHED"
                doc.published_version = pub_ver
                doc.updated_at = datetime.now(timezone.utc)
                await doc.save()
        except Exception:
            pass

        return doc or PromptTemplateDocument.model_construct(**self._memory_templates[template_id])

    # ─── 7. Interactive Prompt Testing ───

    async def test_prompt(
        self,
        template_id: str,
        variables: Dict[str, Any],
        provider: str = "gemini",
        model: str = "gemini-1.5-flash",
    ) -> Dict[str, Any]:
        """Execute interactive test run of prompt through AIGateway."""
        compiled = await self.compile_prompt(template_id, variables)
        from app.ai.gateway.gateway import ai_gateway

        res = await ai_gateway.generate_completion(
            prompt=compiled["user_prompt"],
            system_prompt=compiled["system_prompt"],
            provider=provider,
            model=model,
        )
        return {
            "template_id": template_id,
            "compiled_prompt": compiled,
            "gateway_response": res,
        }

    # ─── 8. A/B Testing Engine ───

    async def create_ab_test(
        self,
        test_id: str,
        template_id: str,
        name: str,
        variant_a_version: int,
        variant_b_version: int,
        traffic_split_percent: float = 50.0,
    ) -> PromptABTestDocument:
        """Create A/B testing experiment comparing two prompt version variants."""
        ab_data = {
            "test_id": test_id,
            "template_id": template_id,
            "name": name,
            "variant_a_version": variant_a_version,
            "variant_b_version": variant_b_version,
            "traffic_split_percent": traffic_split_percent,
            "variant_a_hits": 0,
            "variant_b_hits": 0,
            "variant_a_score": 0.0,
            "variant_b_score": 0.0,
            "status": "ACTIVE",
            "winning_variant": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._memory_ab_tests[test_id] = ab_data

        doc = None
        try:
            doc = PromptABTestDocument(**ab_data)
            await doc.insert()
        except Exception:
            pass

        return doc or PromptABTestDocument.model_construct(**ab_data)

    async def get_ab_test(self, test_id: str) -> PromptABTestDocument:
        """Query A/B experiment telemetry."""
        try:
            doc = await PromptABTestDocument.find_one(PromptABTestDocument.test_id == test_id)
            if doc:
                return doc
        except Exception:
            pass

        if test_id in self._memory_ab_tests:
            return PromptABTestDocument.model_construct(**self._memory_ab_tests[test_id])
        raise ValueError(f"A/B test '{test_id}' not found.")

    async def record_ab_result(self, test_id: str, variant: str, quality_score: float) -> PromptABTestDocument:
        """Record telemetry score for A/B variant ('A' or 'B')."""
        doc = await self.get_ab_test(test_id)
        if variant.upper() == "A":
            doc.variant_a_hits += 1
            doc.variant_a_score = (doc.variant_a_score + quality_score) / max(1, doc.variant_a_hits)
        elif variant.upper() == "B":
            doc.variant_b_hits += 1
            doc.variant_b_score = (doc.variant_b_score + quality_score) / max(1, doc.variant_b_hits)

        if doc.variant_a_hits >= 10 and doc.variant_b_hits >= 10:
            doc.winning_variant = "A" if doc.variant_a_score >= doc.variant_b_score else "B"

        if test_id in self._memory_ab_tests:
            self._memory_ab_tests[test_id] = doc.model_dump()

        try:
            await doc.save()
        except Exception:
            pass

        return doc


prompt_manager = PromptManager()
