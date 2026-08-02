# Enterprise AI Playground Platform — Technical Guide

This guide details the architecture, feature set, REST APIs, and UI Workspace for the **Enterprise AI Playground Platform** in LeadForgeAI.

---

## 1. Feature Specifications

| Feature | Description | Implementation File |
| :--- | :--- | :--- |
| **Multi-Provider Comparison** | Concurrent prompt execution across 2 or 3 model/provider configurations (Gemini, Groq, Mistral, OpenAI, Claude, DeepSeek). | [playground_engine.py](file:///d:/Projects/LeadForgeAI/backend/app/ai/playground/playground_engine.py) |
| **Hyperparameter Controls** | Interactive tuning of temperature ($0.0 - 2.0$), top_p ($0.0 - 1.0$), max_tokens ($1 - 8192$), system prompt, and JSON Mode toggle. | `PlaygroundEngine.execute_single()`, `execute_compare()` |
| **Comparative Telemetry** | Calculates response latency ms, prompt tokens, completion tokens, and estimated USD cost for every provider run. | `PlaygroundEngine.execute_single()` |
| **Session Persistence** | Saves playground sessions (`PlaygroundSessionDocument`) for team audit and history retrieval. | `PlaygroundEngine.save_session()` |
| **Results Export Engine** | Downloads comparative execution results in JSON or formatted Markdown format. | `PlaygroundEngine.export_session_results()` |

---

## 2. REST API Specification

All endpoints are hosted under `/api/v1/ai`:

### `POST /api/v1/ai/playground/execute`
- **Payload**:
  ```json
  {
    "prompt": "Explain quantum computing",
    "provider": "gemini",
    "model": "gemini-1.5-flash",
    "system_prompt": "You are a physics professor.",
    "temperature": 0.5,
    "max_tokens": 1024
  }
  ```

### `POST /api/v1/ai/playground/compare`
- **Payload**:
  ```json
  {
    "prompt": "Synthesize SaaS CFO metrics",
    "targets": [
      { "provider": "gemini", "model": "gemini-1.5-flash" },
      { "provider": "groq", "model": "llama3-70b-8192" },
      { "provider": "mistral", "model": "mistral-large-latest" }
    ],
    "temperature": 0.7
  }
  ```

### `POST /api/v1/ai/playground/sessions`
- **Description**: Persists playground session and model comparison runs.

### `GET /api/v1/ai/playground/sessions`
- **Params**: `limit` (default: 50)
- **Description**: Lists saved playground sessions.

### `POST /api/v1/ai/playground/export`
- **Payload**: `{"session_data": {...}, "format_type": "markdown"}`
- **Description**: Exports comparative results as Markdown or JSON string.

---

## 3. Frontend AI Playground Workspace UI

- **URL Route**: `/ai/playground`
- **Source File**: [AIPlaygroundWorkspace.tsx](file:///d:/Projects/LeadForgeAI/frontend/src/pages/ai/AIPlaygroundWorkspace.tsx)
- **Sections**:
  1. **Mode Switcher**: Toggle between Single Model Testing and Side-by-Side Multi-Provider Comparison Mode.
  2. **Hyperparameters Sidebar**: System prompt text area, Temperature slider, Top P slider, Max Tokens input, JSON Mode checkbox.
  3. **Prompt Composition**: Multiline prompt editor with Session Title input, Save Session, and Export Markdown buttons.
  4. **Side-by-Side Model Outputs Grid**: Real-time response cards displaying model output, Latency ms badge, Tokens count, and USD Cost.

---

## 4. Verification

Run the test suite:
```powershell
$env:PYTHONPATH='d:\Projects\LeadForgeAI\backend'
python scratch/test_enterprise_ai_playground.py
```
