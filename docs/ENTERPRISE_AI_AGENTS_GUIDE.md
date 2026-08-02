# Enterprise AI Agent Platform — Technical Guide

This guide details the architecture, feature set, REST APIs, and UI Workspace for the **Enterprise AI Agent Platform** in LeadForgeAI.

---

## 1. Feature Specifications

| Capability | Description | Implementation File |
| :--- | :--- | :--- |
| **Agent Registry** | Centralized agent catalog managing personas, system prompts, assigned tools, and permission scopes. | [agent_platform.py](file:///d:/Projects/LeadForgeAI/backend/app/ai/agents/agent_platform.py) |
| **Agent Memory** | Short-term goal context synthesis and long-term vector knowledge integration. | `AgentPlatform.run_agent()` |
| **Agent Planning** | Autonomous goal decomposition converting complex user prompts into step-by-step sub-tasks. | `AgentPlatform.plan_task_decomposition()` |
| **Task Decomposition** | Sequential sub-task graph mapping steps to sandboxed tools from `ToolRegistry`. | `AgentPlanDocument.sub_tasks` |
| **Reflection & Self-Evaluation** | Evaluates intermediate outputs, logs step reflections, and computes quality evaluation scores ($0.0 - 1.0$). | `AgentPlatform.reflect_and_evaluate()` |
| **Multi-Agent Collaboration** | Team orchestration, delegation (`delegate_task`), agent messaging, and consensus aggregation. | `AgentPlatform.run_agent_team()` |
| **Agent Permissions** | Scope-based security verification (`crm:*`, `email:send`, `knowledge:read`, `voice:call`). | `AgentDefinition.permission_scopes` |
| **Agent Monitoring & Analytics** | Real-time state machine tracing (`IDLE` ➔ `PLANNING` ➔ `EXECUTING` ➔ `REFLECTING` ➔ `COMPLETED`), run counters, latency, and cost attribution. | `AgentPlatform.get_analytics()` |
| **Agent Marketplace** | Catalog of pre-configured agent templates (`sdr_agent`, `lead_researcher`, `crm_manager`, `outreach_writer`, `data_analyst`) with 1-click installation. | `AgentPlatform.install_marketplace_agent()` |

---

## 2. REST API Specification

All endpoints are hosted under `/api/v1/ai`:

### `GET /api/v1/ai/agents`
- **Description**: Returns list of registered active enterprise agents with status, success rates, and assigned tools.

### `GET /api/v1/ai/agents/marketplace`
- **Description**: Catalog of pre-configured Marketplace agent templates.

### `POST /api/v1/ai/agents/marketplace/install`
- **Payload**: `{"template_id": "sdr_agent"}`
- **Description**: 1-Click install Marketplace agent template.

### `GET /api/v1/ai/agents/metrics`
- **Description**: Returns aggregate agent telemetry analytics.

### `GET /api/v1/ai/agents/{agent_id}`
- **Description**: Returns single agent definition and performance stats.

### `POST /api/v1/ai/agents`
- **Payload**:
  ```json
  {
    "agent_id": "custom_strategist",
    "name": "Custom Strategist",
    "role": "Strategy Lead",
    "description": "Analyzes complex business goals",
    "system_prompt": "You are an AI strategist...",
    "assigned_tools": ["crm_lead_query", "email_send_outreach"],
    "permission_scopes": ["crm:read", "email:send"]
  }
  ```

### `POST /api/v1/ai/agents/{agent_id}/run`
- **Payload**: `{"goal": "Find qualified leads in CRM and send outreach."}`
- **Description**: Executes single autonomous agent run (Planning ➔ Sandboxed Tool Exec ➔ Reflection ➔ Self Evaluation).

### `POST /api/v1/ai/agents/teams/run`
- **Payload**:
  ```json
  {
    "team_name": "Growth SDR Team",
    "participating_agent_ids": ["sdr_agent", "lead_researcher", "outreach_writer"],
    "goal": "Execute Q3 Enterprise Lead Acquisition Campaign."
  }
  ```

---

## 3. Frontend Agent Workspace UI

- **URL Route**: `/ai/agents-platform`
- **Source File**: [AgentWorkspace.tsx](file:///d:/Projects/LeadForgeAI/frontend/src/pages/ai/AgentWorkspace.tsx)
- **Sections**:
  1. **Telemetry Metrics Banner**: Total agents, marketplace templates count, total runs, and overall success rate %.
  2. **Autonomous Agent Runner**: Select agent persona, input goal prompt, view live state step trace, sub-tasks, reflection logs, and quality score.
  3. **Multi-Agent Team Collaborator**: Select team agents, submit goal, view delegation steps and team consensus output.
  4. **Agent Marketplace**: Catalog of verified templates with 1-Click Install buttons.

---

## 4. Verification

Run the test suite:
```powershell
$env:PYTHONPATH='d:\Projects\LeadForgeAI\backend'
python scratch/test_enterprise_ai_agents.py
```
