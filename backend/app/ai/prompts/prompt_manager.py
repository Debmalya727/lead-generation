"""
PromptManager for Phase 12.7A Enterprise AI Gateway.
Handles variable interpolation, template validation, history versioning,
and prompt token compression (whitespaces removal).
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.database.mongodb.collections.ai_gateway import (
    PromptTemplateDocument,
    PromptVersionDocument,
)

logger = logging.getLogger("backend.ai.prompts")


class PromptManager:
    """Enterprise Prompt Template Registry and lifecycle manager."""

    BUILTIN_PROMPTS: List[Dict[str, Any]] = [
        {
            "template_id": "conversation_agent",
            "name": "Conversational CRM Prompt",
            "category": "conversation",
            "system_prompt_template": "You are LeadForgeAI Conversational CRM. You help the user manage leads, research targets, and personalize outreach.",
            "user_prompt_template": "User prompt: {user_prompt}\nMemory context:\n{memory_context}",
            "variables": ["user_prompt", "memory_context"],
        },
        {
            "template_id": "research_summarizer",
            "name": "Research Summary Prompt",
            "category": "research",
            "system_prompt_template": "Summarize target company information into structured insights.",
            "user_prompt_template": "Company Name: {company_name}\nRaw scraped text:\n{scraped_text}",
            "variables": ["company_name", "scraped_text"],
        },
        {
            "template_id": "outreach_personalized",
            "name": "Outreach Generation Prompt",
            "category": "outreach",
            "system_prompt_template": "Generate high-converting, personalized cold email outreach.",
            "user_prompt_template": "Lead: {lead_name}\nCompany: {company_name}\nPain Points: {pain_points}",
            "variables": ["lead_name", "company_name", "pain_points"],
        },
    ]

    async def initialize_builtin_prompts(self) -> None:
        """Seed default prompts into MongoDB if not present."""
        for bp in self.BUILTIN_PROMPTS:
            try:
                doc = await PromptTemplateDocument.find_one(
                    PromptTemplateDocument.template_id == bp["template_id"]
                )
                if not doc:
                    doc = PromptTemplateDocument(**bp)
                    await doc.insert()
                    
                    # Create version 1
                    ver = PromptVersionDocument(
                        template_id=bp["template_id"],
                        version=1,
                        system_prompt=bp["system_prompt_template"],
                        user_prompt=bp["user_prompt_template"],
                        changes_description="Initial seed version",
                    )
                    await ver.insert()
                    logger.info(f"PromptManager: Seeded prompt template '{bp['template_id']}'")
            except Exception as e:
                logger.warning(f"Error seeding prompt '{bp['template_id']}': {str(e)}")

    async def get_prompt(self, template_id: str, variables: Dict[str, Any]) -> Dict[str, str]:
        """
        Substitutes variables into template and returns compiled system & user prompts.
        Throws error if missing required variables.
        """
        doc = await PromptTemplateDocument.find_one(PromptTemplateDocument.template_id == template_id)
        if not doc:
            raise ValueError(f"Prompt template '{template_id}' not found.")

        # Check required variables
        for var in doc.variables:
            if var not in variables or variables[var] is None:
                raise ValueError(f"Prompt variables dictionary missing required key: '{var}'")

        # Substitute
        user_prompt = doc.user_prompt_template.format(**variables)
        system_prompt = doc.system_prompt_template.format(**variables) if doc.system_prompt_template else ""

        # Compress to optimize token usage
        user_prompt = self.compress_prompt(user_prompt)
        system_prompt = self.compress_prompt(system_prompt)

        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
        }

    def compress_prompt(self, prompt_text: str) -> str:
        """Compresses prompt text by removing duplicate whitespaces and empty lines."""
        if not prompt_text:
            return ""
        lines = [line.strip() for line in prompt_text.split("\n")]
        # Remove empty lines and join
        cleaned_lines = [line for line in lines if line]
        return "\n".join(cleaned_lines)

    async def save_template(
        self,
        template_id: str,
        name: str,
        category: str,
        user_prompt_template: str,
        system_prompt_template: Optional[str] = None,
        variables: Optional[List[str]] = None,
        changes_description: Optional[str] = None,
    ) -> PromptTemplateDocument:
        """Create or update a prompt template, saving historical version."""
        variables = variables or []
        doc = await PromptTemplateDocument.find_one(PromptTemplateDocument.template_id == template_id)
        
        if not doc:
            doc = PromptTemplateDocument(
                template_id=template_id,
                name=name,
                category=category,
                user_prompt_template=user_prompt_template,
                system_prompt_template=system_prompt_template,
                variables=variables,
            )
            await doc.insert()
            next_ver = 1
        else:
            doc.name = name
            doc.category = category
            doc.user_prompt_template = user_prompt_template
            doc.system_prompt_template = system_prompt_template
            doc.variables = variables
            await doc.save()

            # Determine next version number
            latest_version = await PromptVersionDocument.find(
                PromptVersionDocument.template_id == template_id
            ).sort("-version").first()
            next_ver = (latest_version.version + 1) if latest_version else 1

        # Save version history log
        ver = PromptVersionDocument(
            template_id=template_id,
            version=next_ver,
            system_prompt=system_prompt_template,
            user_prompt=user_prompt_template,
            changes_description=changes_description or f"Update to version {next_ver}",
        )
        await ver.insert()
        return doc


prompt_manager = PromptManager()
