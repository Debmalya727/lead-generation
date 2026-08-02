"""
Content processor for website text extraction results.

Handles:
- HTML cleaning and normalization
- Intelligent text chunking by paragraph/sentence boundaries
- LLM prompt assembly for structured intelligence extraction
"""
import re
import logging
from typing import List

logger = logging.getLogger("backend.intelligence.content_processor")

# System prompt for the LLM to follow
INTELLIGENCE_SYSTEM_PROMPT = """You are a world-class B2B sales intelligence analyst. Your job is to analyze any available business data and produce detailed, actionable intelligence reports for enterprise sales teams.

CRITICAL RULES:
1. Return ONLY a valid JSON object — no markdown fences, no explanations, no preamble.
2. ALWAYS populate every field with your best analysis. NEVER return empty arrays or null for all fields — use your expert business knowledge to infer what is not explicitly stated.
3. If the website was blocked by a firewall (Akamai, Cloudflare) or is a hotel/chain, use your training data about that brand to complete the analysis.
4. Be SPECIFIC — include real product names, service categories, pain points relevant to this industry.
5. The executive_summary must always have at least 2 rich, specific sentences.
6. confidence_score: 85+ if you have good data, 65-84 if inferred from brand knowledge, 50-64 if minimal data."""

INTELLIGENCE_PROMPT_TEMPLATE = """Analyze the business data below for "{company_name}" (website: {website_url}) and produce a complete B2B sales intelligence report.

AVAILABLE DATA:
---
{content}
---

INSTRUCTIONS:
- If the company is a well-known brand (hotel chain, restaurant group, etc.), use your comprehensive knowledge about them.
- Infer pain points from the industry vertical, not just the text above.
- Buying signals should reflect realistic vendor opportunities for this type of business.
- ideal_sales_angle must be a specific, personalized 1-2 sentence cold outreach hook.

Return a JSON object with EXACTLY these fields:
{{
  "executive_summary": "<2 specific sentences describing what this company does and who they serve — be descriptive>",
  "company_description": "<detailed 3-4 sentence paragraph covering the business, its history, scale, and value proposition>",
  "products": ["<specific product 1>", "<specific product 2>", "<specific product 3>"],
  "services": ["<specific service 1>", "<specific service 2>", "<specific service 3>"],
  "industry": "<primary industry vertical e.g. 'Luxury Hospitality', 'B2B SaaS', 'Manufacturing'>",
  "company_size": "<estimated headcount range e.g. '500-2000 employees'>",
  "revenue_estimate": "<estimated annual revenue range e.g. '$10M-$50M USD'>",
  "revenue_confidence": "<low, medium, or high>",
  "pain_points": ["<specific operational pain point 1>", "<specific pain point 2>", "<specific pain point 3>"],
  "buying_signals": ["<vendor opportunity signal 1>", "<vendor opportunity signal 2>", "<vendor opportunity signal 3>"],
  "ideal_sales_angle": "<specific personalized cold outreach hook for a sales rep targeting this company>",
  "confidence_score": <integer 0-100>
}}

Return only the JSON object. No markdown. No explanation."""


class ContentProcessor:
    """Processes raw website text content for LLM-ready analysis."""

    def chunk_text(self, text: str, max_chars: int = 8000) -> List[str]:
        """
        Split text into chunks respecting paragraph boundaries.
        Prevents mid-sentence splits by preferring paragraph breaks.
        """
        if len(text) <= max_chars:
            return [text]

        chunks = []
        # Split by double newlines (paragraph breaks) first
        paragraphs = re.split(r"\n{2,}", text)
        current_chunk = []
        current_length = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_len = len(para)

            # If adding this paragraph would exceed limit, flush current chunk
            if current_length + para_len + 2 > max_chars and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_length = 0

            # If a single paragraph exceeds max, split at sentence boundaries
            if para_len > max_chars:
                sentences = re.split(r"(?<=[.!?])\s+", para)
                for sentence in sentences:
                    s_len = len(sentence)
                    if current_length + s_len + 1 > max_chars and current_chunk:
                        chunks.append("\n\n".join(current_chunk))
                        current_chunk = []
                        current_length = 0
                    current_chunk.append(sentence)
                    current_length += s_len + 1
            else:
                current_chunk.append(para)
                current_length += para_len + 2

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        logger.debug(f"Chunked {len(text)} chars into {len(chunks)} chunk(s)")
        return chunks

    def build_analysis_prompt(
        self,
        text_content: str,
        company_name: str,
        website_url: str,
        max_content_chars: int = 8000
    ) -> str:
        """
        Build the full LLM prompt by capping content length to fit model context window.
        Uses the first (most important) chunk if content is very long.
        """
        # Use the first chunk since homepage + key pages are typically at the start
        content_to_use = text_content[:max_content_chars].strip()

        return INTELLIGENCE_PROMPT_TEMPLATE.format(
            company_name=company_name,
            website_url=website_url,
            content=content_to_use,
        )

    def get_system_prompt(self) -> str:
        """Return the system prompt for the LLM."""
        return INTELLIGENCE_SYSTEM_PROMPT

    def clean_llm_response(self, response: str) -> str:
        """
        Strip any markdown code fences from the LLM response to get pure JSON.
        Some models wrap output in ```json ... ``` despite being told not to.
        """
        response = response.strip()
        # Remove markdown code block wrappers
        response = re.sub(r"^```(?:json)?\s*", "", response)
        response = re.sub(r"\s*```$", "", response)
        return response.strip()
