"""
Built-in default policy rules for Phase 12.7B AI Policy Engine.
Maps capabilities to providers/models with priorities.
These are seeded into MongoDB on startup if no policies exist.
"""
from typing import List
from app.ai.policies.schemas import PolicyRule, PolicyCondition, PolicyAction

DEFAULT_POLICY_RULES: List[PolicyRule] = [
    PolicyRule(
        policy_id="policy_reasoning_001",
        name="Reasoning → Claude Sonnet",
        capability="reasoning",
        priority=10,
        conditions=PolicyCondition(),
        action=PolicyAction(provider="claude", model="claude-3-5-sonnet"),
        description="Route all reasoning tasks to Claude Sonnet for superior chain-of-thought."
    ),
    PolicyRule(
        policy_id="policy_vision_001",
        name="Vision → GPT-4o",
        capability="vision",
        priority=10,
        conditions=PolicyCondition(),
        action=PolicyAction(provider="openai", model="gpt-4o"),
        description="Route all image/visual tasks to GPT-4o."
    ),
    PolicyRule(
        policy_id="policy_embedding_001",
        name="Embedding → OpenAI",
        capability="embedding",
        priority=10,
        conditions=PolicyCondition(),
        action=PolicyAction(provider="openai", model="text-embedding-3-small"),
        description="Route all embedding requests to OpenAI text-embedding-3-small."
    ),
    PolicyRule(
        policy_id="policy_cheap_chat_001",
        name="Cheap Chat → Gemini Flash",
        capability="chat",
        priority=20,
        conditions=PolicyCondition(),
        action=PolicyAction(provider="gemini", model="gemini-1.5-flash"),
        description="Low-cost conversational tasks routed to Gemini Flash."
    ),
    PolicyRule(
        policy_id="policy_coding_001",
        name="Coding → Claude Sonnet",
        capability="coding",
        priority=10,
        conditions=PolicyCondition(),
        action=PolicyAction(provider="claude", model="claude-3-5-sonnet"),
        description="Route code generation to Claude Sonnet for high reliability."
    ),
    PolicyRule(
        policy_id="policy_json_generation_001",
        name="JSON Generation → GPT-4o Mini",
        capability="json_generation",
        priority=10,
        conditions=PolicyCondition(),
        action=PolicyAction(provider="openai", model="gpt-4o-mini"),
        description="Route JSON extraction/generation tasks to GPT-4o Mini for structured output reliability."
    ),
    PolicyRule(
        policy_id="policy_long_context_001",
        name="Long Context → Gemini Pro",
        capability="long_context",
        priority=10,
        conditions=PolicyCondition(),
        action=PolicyAction(provider="gemini", model="gemini-1.5-pro"),
        description="Route long document tasks to Gemini 1.5 Pro for 2M token context window."
    ),
    PolicyRule(
        policy_id="policy_research_001",
        name="Research → Gemini Pro",
        capability="research",
        priority=10,
        conditions=PolicyCondition(),
        action=PolicyAction(provider="gemini", model="gemini-1.5-pro"),
        description="Route research tasks to Gemini Pro for large context summarization."
    ),
    PolicyRule(
        policy_id="policy_summarization_001",
        name="Summarization → Gemini Flash",
        capability="summarization",
        priority=10,
        conditions=PolicyCondition(),
        action=PolicyAction(provider="gemini", model="gemini-1.5-flash"),
        description="Efficient summarization via Gemini Flash."
    ),
    PolicyRule(
        policy_id="policy_tool_calling_001",
        name="Tool Calling → GPT-4o Mini",
        capability="tool_calling",
        priority=10,
        conditions=PolicyCondition(),
        action=PolicyAction(provider="openai", model="gpt-4o-mini"),
        description="Tool-augmented calls routed to GPT-4o Mini for reliable function calling."
    ),
    PolicyRule(
        policy_id="policy_translation_001",
        name="Translation → Gemini Flash",
        capability="translation",
        priority=10,
        conditions=PolicyCondition(),
        action=PolicyAction(provider="gemini", model="gemini-1.5-flash"),
        description="Translation tasks routed to Gemini Flash."
    ),
    PolicyRule(
        policy_id="policy_planning_001",
        name="Planning → Claude Sonnet",
        capability="planning",
        priority=10,
        conditions=PolicyCondition(),
        action=PolicyAction(provider="claude", model="claude-3-5-sonnet"),
        description="Multi-step planning tasks routed to Claude Sonnet."
    ),
]
