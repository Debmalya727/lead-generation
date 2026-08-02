# Enterprise Prompt Management Platform — Technical Guide

This guide details the architecture, feature set, REST APIs, and UI Workspace for the **Enterprise Prompt Management Platform** in LeadForgeAI.

---

## 1. Feature Specifications

| Feature | Description | Implementation File |
| :--- | :--- | :--- |
| **Prompt Library** | Catalog of all prompt templates across enterprise categories. | [PromptManager](file:///d:/Projects/LeadForgeAI/backend/app/ai/prompts/prompt_manager.py) |
| **Prompt Templates** | System instruction & user prompt template definitions. | [PromptTemplateDocument](file:///d:/Projects/LeadForgeAI/backend/app/database/mongodb/collections/ai_gateway.py) |
| **Versioning** | Immutable revision history (`v1.0.0`, `v1.1.0`) with author logs. | `PromptVersionDocument` |
| **Variables Engine** | Auto extraction & compilation of `{var}` and `{{var}}` placeholders. | `PromptManager.extract_variables()` |
| **Prompt Testing** | Interactive execution playground running completions through `ai_gateway`. | `PromptManager.test_prompt()` |
| **Prompt Approval** | Approval state machine (`DRAFT` ➔ `IN_REVIEW` ➔ `APPROVED` ➔ `REJECTED`). | `PromptManager.update_approval()` |
| **Prompt Publishing** | Production release management (`PUBLISHED` version pinning). | `PromptManager.publish_version()` |
| **Prompt Rollback** | 1-Click reversion to any historical version snapshot. | `PromptManager.rollback_version()` |
| **Prompt Analytics** | Tracks hit counts, average ratings, and execution telemetry. | `PromptTemplateDocument.hit_count` |
| **Prompt A/B Testing** | Variant comparison (`Variant A` vs `Variant B`), split traffic, and winner calculation. | [PromptABTestDocument](file:///d:/Projects/LeadForgeAI/backend/app/database/mongodb/collections/ai_gateway.py) |
| **Prompt Security** | Sanitization against prompt injection attacks (`system override`, `ignore previous`). | `PromptManager.sanitize_prompt()` |
| **Prompt Diff Viewer** | Unified text diff comparison between two version revisions. | `PromptManager.generate_diff()` |
| **Tags & Categories** | Multi-attribute taxonomy search (`outreach`, `crm`, `summary`, `scoring`, `#b2b`). | `PromptManager.list_templates()` |

---

## 2. REST API Specification

All endpoints are hosted under `/api/v1/ai`:

### `GET /api/v1/ai/prompts`
- **Params**: `query`, `category`, `tag`, `status`
- **Description**: Search and list prompt templates matching multi-attribute filters.

### `GET /api/v1/ai/prompts/{template_id}`
- **Description**: Fetch prompt template details by ID.

### `POST /api/v1/ai/prompts`
- **Payload**:
  ```json
  {
    "template_id": "outreach_personalized",
    "name": "Outreach Generation Prompt",
    "category": "outreach",
    "tags": ["email", "sales"],
    "user_prompt_template": "Hi {first_name}, {company_name} is growing...",
    "system_prompt_template": "You are a sales SDR copywriter.",
    "changes_description": "Updated value proposition wording"
  }
  ```

### `GET /api/v1/ai/prompts/{template_id}/history`
- **Description**: Returns ordered version revision history.

### `GET /api/v1/ai/prompts/{template_id}/diff?version_a=1&version_b=2`
- **Description**: Returns unified text diff lines comparing two prompt versions.

### `POST /api/v1/ai/prompts/{template_id}/rollback`
- **Payload**: `{"target_version": 1}`
- **Description**: Restores template content from target version as a new version revision.

### `POST /api/v1/ai/prompts/{template_id}/approval`
- **Payload**: `{"status": "APPROVED"}`

### `POST /api/v1/ai/prompts/{template_id}/publish`
- **Payload**: `{"version": 2}`

### `POST /api/v1/ai/prompts/{template_id}/test`
- **Payload**:
  ```json
  {
    "variables": {"first_name": "Sarah", "company_name": "Acme Corp"},
    "provider": "gemini",
    "model": "gemini-1.5-flash"
  }
  ```

### `POST /api/v1/ai/prompts/ab-tests`
- **Payload**:
  ```json
  {
    "test_id": "ab_test_01",
    "template_id": "outreach_personalized",
    "name": "Outreach V1 vs V2",
    "variant_a_version": 1,
    "variant_b_version": 2,
    "traffic_split_percent": 50.0
  }
  ```

---

## 3. Frontend Workspace UI

- **URL Route**: `/ai/prompts`
- **Source File**: [PromptWorkspace.tsx](file:///d:/Projects/LeadForgeAI/frontend/src/pages/ai/PromptWorkspace.tsx)
- **Sections**:
  1. **Sidebar Catalog**: Quick search, category & status dropdown filters.
  2. **Template Editor**: Live variable extraction, system/user prompt fields, commit message log, and Approval/Publish buttons.
  3. **Testing Playground**: Interactive test variable inputs, provider selection, and live completion preview.
  4. **Version History & Diff Viewer**: Commit history list, 1-click **Rollback**, and **Compare Diff** preview.

---

## 4. Verification

Run the test suite:
```powershell
$env:PYTHONPATH='d:\Projects\LeadForgeAI\backend'
python scratch/test_prompt_platform_enterprise.py
```
