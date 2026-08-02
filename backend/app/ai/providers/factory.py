"""
LLM Provider Factory — reads environment variables to instantiate multi-agent providers.

Architecture Model Routing (User's Exact Config):
- Manager:          OpenRouter | nvidia/nemotron-3-ultra
- Planner:          Groq       | gpt-oss-20b
- Scraper:          Ollama     | qwen3.5        (Cloud endpoint via OLLAMA_BASE_URL)
- Research:         Groq       | llama-3.3-70b
- Website Analyzer: Ollama     | gemma4:12b     (Cloud endpoint via OLLAMA_BASE_URL)
- Lead Scorer:      Groq       | llama-3.3-70b
- Outreach:         OpenRouter | nvidia/nemotron-3-ultra
- Fallback:         OpenRouter | openrouter/free
"""
import logging
import os
from typing import Optional
from app.ai.providers.base_llm import BaseLLMProvider

logger = logging.getLogger("backend.ai.factory")


class AIGatewayLLMProvider(BaseLLMProvider):
    """LLM provider wrapper routing all requests through the central AI Gateway."""

    def __init__(self, provider: str, model: str, agent_type: Optional[str] = None):
        self.provider = provider
        self.model = model
        self.agent_type = agent_type or "general"
        self.model_name = model  # alias for display/verification

    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        from app.ai.gateway.gateway import ai_gateway
        res = await ai_gateway.generate_completion(
            prompt=prompt,
            system_prompt=system_prompt,
            provider=self.provider,
            model=self.model,
            agent_id=self.agent_type,
            bypass_cache=True,
        )
        return res["response_text"]


def get_llm_provider(agent_type: Optional[str] = None) -> BaseLLMProvider:
    """
    Factory function returning the configured LLM provider instance for a specific agent role.
    Uses the user's exact multi-agent model configuration from environment variables.
    Falls back gracefully when Ollama cloud is unreachable.
    """
    agent = (agent_type or "").lower().strip()

    # -----------------------------------------------------------------
    # 🧠 Manager / Executive / Orchestrator — OpenRouter | Nemotron-3 Ultra
    # -----------------------------------------------------------------
    if agent in ("manager", "executive", "orchestrator"):
        provider_name = os.getenv("MANAGER_AGENT_PROVIDER", "openrouter").strip()
        model = os.getenv("MANAGER_AGENT_MODEL", "nvidia/nemotron-3-ultra").strip()

    # -----------------------------------------------------------------
    # 🛑 Memory Agent — shares Manager provider (reasoning-heavy)
    # -----------------------------------------------------------------
    elif agent == "memory":
        provider_name = os.getenv("MANAGER_AGENT_PROVIDER", "openrouter").strip()
        model = os.getenv("MANAGER_AGENT_MODEL", "nvidia/nemotron-3-ultra").strip()

    # -----------------------------------------------------------------
    # 📋 Planner Agent — Groq | gpt-oss-20b
    # -----------------------------------------------------------------
    elif agent in ("planner", "scheduler"):
        provider_name = os.getenv("PLANNER_AGENT_PROVIDER", "groq").strip()
        model = os.getenv("PLANNER_AGENT_MODEL", "gpt-oss-20b").strip()

    # -----------------------------------------------------------------
    # 🕷️ Scraper Agent — Ollama Cloud | qwen3.5
    # -----------------------------------------------------------------
    elif agent in ("scraper", "crawler"):
        provider_name = os.getenv("SCRAPER_AGENT_PROVIDER", "ollama").strip()
        model = os.getenv("SCRAPER_AGENT_MODEL", "qwen3.5").strip()

    # -----------------------------------------------------------------
    # 🔎 Research Agent — Groq | llama-3.3-70b
    # -----------------------------------------------------------------
    elif agent in ("research", "researcher"):
        provider_name = os.getenv("RESEARCH_AGENT_PROVIDER", "groq").strip()
        model = os.getenv("RESEARCH_AGENT_MODEL", "llama-3.3-70b").strip()

    # -----------------------------------------------------------------
    # 🌐 Website Analyzer — Ollama Cloud | gemma4:12b
    #    Auto-falls back to Groq/llama-3.3-70b if OLLAMA_BASE_URL is not set
    # -----------------------------------------------------------------
    elif agent in ("website_analyzer", "analyzer", "review"):
        provider_name = os.getenv("WEBSITE_ANALYZER_PROVIDER", "ollama").strip()
        model = os.getenv("WEBSITE_ANALYZER_MODEL", "gemma4:12b").strip()

        # Smart fallback: if Ollama base URL is a placeholder or not configured, use Groq
        ollama_base = os.getenv("OLLAMA_BASE_URL", "").strip()
        is_ollama_placeholder = (
            not ollama_base
            or "your-ollama-cloud-endpoint" in ollama_base
            or ollama_base == "http://localhost:11434"
        )
        if provider_name == "ollama" and is_ollama_placeholder:
            logger.warning(
                "WEBSITE_ANALYZER: OLLAMA_BASE_URL is not configured. "
                "Auto-switching to Groq/llama-3.3-70b as fallback."
            )
            provider_name = "groq"
            model = "llama-3.3-70b-versatile"

    # -----------------------------------------------------------------
    # 🎯 Lead Scorer Agent — Groq | llama-3.3-70b
    # -----------------------------------------------------------------
    elif agent in ("lead_scorer", "scorer"):
        provider_name = os.getenv("LEAD_SCORER_PROVIDER", "groq").strip()
        model = os.getenv("LEAD_SCORER_MODEL", "llama-3.3-70b").strip()

    # -----------------------------------------------------------------
    # ✉️ Outreach Agent — OpenRouter | nvidia/nemotron-3-ultra
    # -----------------------------------------------------------------
    elif agent in ("outreach", "sales_writer"):
        provider_name = os.getenv("OUTREACH_AGENT_PROVIDER", "openrouter").strip()
        model = os.getenv("OUTREACH_AGENT_MODEL", "nvidia/nemotron-3-ultra").strip()

    # -----------------------------------------------------------------
    # 🛟 Fallback Engine — OpenRouter | openrouter/free
    # -----------------------------------------------------------------
    elif agent == "fallback":
        provider_name = os.getenv("FALLBACK_PROVIDER", "openrouter").strip()
        model = os.getenv("FALLBACK_MODEL", "openrouter/free").strip()

    # -----------------------------------------------------------------
    # Generic / Unrecognized — uses LLM_PROVIDER env, never "mock"
    # -----------------------------------------------------------------
    else:
        provider_name = os.getenv("LLM_PROVIDER", "openrouter").lower().strip()
        if provider_name == "mock":
            # Never use mock — silently upgrade to OpenRouter
            provider_name = "openrouter"
        model = os.getenv("LLM_MODEL", "nvidia/nemotron-3-ultra").strip()

    logger.info(
        f"Factory routing get_llm_provider(agent_type='{agent_type}') "
        f"-> provider={provider_name}, model={model}"
    )
    return AIGatewayLLMProvider(provider=provider_name, model=model, agent_type=agent_type)
