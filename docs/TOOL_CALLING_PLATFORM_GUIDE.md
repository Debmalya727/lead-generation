# Enterprise AI Tool Calling Platform — Technical Guide

This guide details the architecture, tool registry, security sandbox, REST APIs, and UI Workspace for the **Enterprise AI Tool Calling Platform** in LeadForgeAI.

---

## 1. Feature Specifications

| Component | Description | Implementation File |
| :--- | :--- | :--- |
| **Tool Registry** | Centralized tool management, versioning (`v1.0.0`), permission scope tags, and multi-provider schema exporters. | [tool_registry.py](file:///d:/Projects/LeadForgeAI/backend/app/ai/tools/tool_registry.py) |
| **Tool Sandbox** | Security execution bridge enforcing permission verification, argument validation, timeout barriers, and audit logging. | [tool_sandbox.py](file:///d:/Projects/LeadForgeAI/backend/app/ai/tools/tool_sandbox.py) |
| **Direct Execution Barrier** | Direct tool execution is forbidden. Every AI Provider routes calls exclusively through `tool_sandbox.execute_tool()`. | [gateway.py](file:///d:/Projects/LeadForgeAI/backend/app/ai/gateway/gateway.py) |
| **Tool Permissions** | Scope-based security verification (`crm:read`, `crm:write`, `email:send`, `voice:call`, `db:read`, `workflow:execute`). | `ToolSandbox.validate_permissions()` |
| **Tool Validation** | JSON Schema input argument verification before handler invocation. | `ToolSandbox.validate_arguments()` |
| **Tool Logs & Metrics** | Execution audit logs (`ToolExecutionLogDocument`) and live telemetry metrics (call volume, latency ms, success rate %). | `ToolRegistry.get_metrics()` |

---

## 2. 9 Registered Enterprise Tool Suites

Registered in [enterprise_tools.py](file:///d:/Projects/LeadForgeAI/backend/app/ai/tools/enterprise_tools.py):

1. **CRM**: `crm_lead_query`, `crm_lead_update` (scopes: `crm:read`, `crm:write`)
2. **Knowledge**: `knowledge_search`, `knowledge_ingest` (scopes: `knowledge:read`, `knowledge:write`)
3. **Calendar**: `calendar_schedule_meeting`, `calendar_get_availability` (scopes: `calendar:write`, `calendar:read`)
4. **Email**: `email_send_outreach`, `email_template_fetch` (scopes: `email:send`, `email:read`)
5. **Voice**: `voice_call_initiate`, `voice_transcript_analyze` (scopes: `voice:call`, `voice:read`)
6. **Search**: `web_search_query` (scope: `search:read`)
7. **Database**: `database_read_records` (scope: `db:read`)
8. **Analytics**: `analytics_query_metrics` (scope: `analytics:read`)
9. **Workflow**: `workflow_trigger_execution` (scope: `workflow:execute`)

---

## 3. REST API Specification

All endpoints are hosted under `/api/v1/ai`:

### `GET /api/v1/ai/tools`
- **Params**: `category` (optional filter)
- **Description**: Returns registered tools with parameter schemas, scopes, versions, and latency/call metrics.

### `GET /api/v1/ai/tools/schemas/openai`
- **Description**: Export registered tools formatted in OpenAI standard function calling schema.

### `GET /api/v1/ai/tools/schemas/gemini`
- **Description**: Export registered tools formatted in Google Gemini function declaration schema.

### `GET /api/v1/ai/tools/metrics`
- **Description**: Returns system-wide tool call volume, error count, and success rate % metrics.

### `GET /api/v1/ai/tools/logs`
- **Params**: `limit` (default: 50)
- **Description**: Audit execution history showing correlation ID, duration, status, and input args.

### `POST /api/v1/ai/tools/execute`
- **Payload**:
  ```json
  {
    "tool_name": "crm_lead_query",
    "arguments": {"search_query": "Acme Corp", "min_score": 80},
    "user_scopes": ["crm:read"]
  }
  ```
- **Description**: Executes a tool through the security sandbox execution bridge.

---

## 4. Frontend Tool Workspace UI

- **URL Route**: `/ai/tools`
- **Source File**: [ToolWorkspace.tsx](file:///d:/Projects/LeadForgeAI/frontend/src/pages/ai/ToolWorkspace.tsx)
- **Sections**:
  1. **Telemetry Metrics Banner**: Total tools, call volume, overall success rate, and security status.
  2. **Registered Tool Catalog**: Sidebar list across all 9 domains with search & category filters.
  3. **Multi-Provider Schema Inspector**: Native, OpenAI, and Gemini schema tabs.
  4. **Sandboxed Execution Tester**: Arguments JSON input, scope configuration, and live result view.
  5. **Real-Time Execution Audit Logs Table**: Trace table of recent execution calls.

---

## 5. Verification

Run the test suite:
```powershell
$env:PYTHONPATH='d:\Projects\LeadForgeAI\backend'
python scratch/test_tool_calling_platform_enterprise.py
```
