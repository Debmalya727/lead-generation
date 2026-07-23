"""
Autonomous LLM-based multi-agent workflow systems.
"""

# Import agents to trigger @register_agent registration at startup
import app.agents.models.diagnostic_agent  # Built-in diagnostic agent

# Phase 11 Milestone 2 — Business Agents
import app.agents.business.research_agent
import app.agents.business.memory_agent
import app.agents.business.sales_strategy_agent
import app.agents.business.outreach_agent
import app.agents.business.review_agent
import app.agents.business.executive_agent
