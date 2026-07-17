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
INTELLIGENCE_SYSTEM_PROMPT = """You are an expert business analyst and sales intelligence researcher.
You analyze website content and extract structured business intelligence useful for B2B sales teams.

CRITICAL RULES:
1. Return ONLY valid JSON — no explanations, no markdown code blocks, no extra text.
2. If you cannot determine a field with reasonable confidence, use null for strings or [] for arrays.
3. Be concise but specific — avoid generic filler phrases.
4. Base all analysis strictly on the provided website content.
5. The confidence_score (0-100) reflects how much useful sales intelligence you found.
"""

INTELLIGENCE_PROMPT_TEMPLATE = """Analyze the following website content for "{company_name}" ({website_url}) 
and extract structured business intelligence for a B2B sales team.

WEBSITE CONTENT:
---
{content}
---

Return a JSON object with EXACTLY these fields (no additional fields):
{{
  "executive_summary": "<1-2 sentence snapshot of what this company does and who they serve>",
  "company_description": "<detailed paragraph describing the company>",
  "products": ["<specific product 1>", "<specific product 2>"],
  "services": ["<specific service 1>", "<specific service 2>"],
  "industry": "<primary industry vertical>",
  "company_size": "<estimated headcount range, e.g. '10-50 employees' or null if unknown>",
  "revenue_estimate": "<estimated annual revenue range or null if unknown>",
  "revenue_confidence": "<low, medium, or high>",
  "pain_points": ["<pain point 1 likely faced by this company>", "<pain point 2>"],
  "buying_signals": ["<buying signal 1 indicating they might be open to vendors>", "<buying signal 2>"],
  "ideal_sales_angle": "<specific recommended approach for a sales rep to use when engaging this company>",
  "confidence_score": <integer 0-100 reflecting how complete and useful the extracted intelligence is>
}}

Return only the JSON object."""


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
