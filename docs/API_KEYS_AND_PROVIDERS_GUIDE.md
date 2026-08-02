# LeadForgeAI — API Keys & External Provider Configuration Guide

> **Enterprise AI & Email Service Providers Integration Document**

---

## 1. Configured Environment Variables Overview

LeadForgeAI supports **10 AI Provider Adapters** and **4 Email Delivery Providers**. All API keys and connection credentials are dynamically loaded from `backend/.env` without requiring hardcoded secrets.

| Provider | Environment Variable | Config Status | Default Model / Target |
| :--- | :--- | :--- | :--- |
| **Google Gemini** | `GEMINI_API_KEY` | **CONFIGURED** | `gemini-1.5-flash` |
| **Groq AI** | `GROQ_API_KEY` | **CONFIGURED** | `llama-3.3-70b-versatile` |
| **Mistral AI** | `MISTRAL_API_KEY` | **CONFIGURED** | `mistral-small-latest` |
| **OpenRouter** | `OPENROUTER_API_KEY` | **CONFIGURED** | `meta-llama/llama-3.1-8b-instruct:free` |
| **Resend Email** | `RESEND_API_KEY` | **CONFIGURED** | Transactional & Campaign Email API |
| **OpenAI** | `OPENAI_API_KEY` | *Optional* | `gpt-4o-mini` |
| **Anthropic Claude** | `CLAUDE_API_KEY` | *Optional* | `claude-3-5-sonnet` |
| **DeepSeek** | `DEEPSEEK_API_KEY` | *Optional* | `deepseek-chat` |
| **Ollama** | N/A (Local) | *Local Instance* | `http://localhost:11434` |
| **vLLM** | N/A (Local) | *Local Instance* | `http://localhost:8000/v1` |

---

## 2. API Key Obtaining & Setup Instructions

### A. Google Gemini API (`GEMINI_API_KEY`)
1. Visit Google AI Studio: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Click **Create API Key**.
3. Select your Google Cloud Project.
4. Copy the generated key and add to `.env`:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

### B. Groq AI (`GROQ_API_KEY`)
1. Access Groq Console: [https://console.groq.com/keys](https://console.groq.com/keys)
2. Click **Create API Key**.
3. Copy the key starting with `gsk_...` and set in `.env`:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

### C. Mistral AI (`MISTRAL_API_KEY`)
1. Open Mistral La Plateforme: [https://console.mistral.ai/api-keys/](https://console.mistral.ai/api-keys/)
2. Generate a new key and add to `.env`:
   ```env
   MISTRAL_API_KEY=your_mistral_api_key_here
   ```

### D. OpenRouter (`OPENROUTER_API_KEY`)
1. Open OpenRouter Keys Page: [https://openrouter.ai/keys](https://openrouter.ai/keys)
2. Create a new token starting with `sk-or-v1-...` and set in `.env`:
   ```env
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```

### E. Resend Email (`RESEND_API_KEY`)
1. Open Resend Dashboard: [https://resend.com/api-keys](https://resend.com/api-keys)
2. Create Full Access API Key starting with `re_...` and set in `.env`:
   ```env
   RESEND_API_KEY=your_resend_api_key_here
   ```

---

## 3. Team Prompts for Requesting Additional API Keys

If you need to request keys from your project manager, client, or security lead, copy and send the prompts below:

### Prompt 1: Requesting OpenAI / Anthropic / DeepSeek Keys
```text
Hi Team,

To activate dedicated OpenAI (GPT-4o), Anthropic (Claude 3.5 Sonnet), and DeepSeek reasoning capabilities in LeadForgeAI, please provide the following environment API keys:

1. OPENAI_API_KEY (from https://platform.openai.com/api-keys)
2. CLAUDE_API_KEY (from https://console.anthropic.com/settings/keys)
3. DEEPSEEK_API_KEY (from https://platform.deepseek.com/api_keys)

Once provided, we will insert them into backend/.env. Currently, Gemini, Groq, Mistral, OpenRouter, and Resend are fully active.
```

### Prompt 2: Requesting Custom Domain Email Sender for Resend
```text
Hi Team,

Our Resend Email Integration is live in LeadForgeAI (RESEND_API_KEY=your_resend_api_key_here). 

To send outreach emails directly from your company domain (e.g., outreach@yourcompany.com) instead of the default test domain (onboarding@resend.dev):
1. Log into https://resend.com/domains
2. Add your domain and add the DNS TXT/MX records to your domain provider.
3. Update the DEFAULT_FROM_EMAIL in LeadForgeAI settings.
```

---

## 4. Automatic Startup Key Validation

When LeadForgeAI backend starts (`uvicorn app.main:app`), it automatically executes non-crashing startup validation:

```text
🔑 [API Key Startup Validation] Configured keys (5): GEMINI_API_KEY, GROQ_API_KEY, MISTRAL_API_KEY, OPENROUTER_API_KEY, RESEND_API_KEY
⚠️ [API Key Startup Validation] Missing keys (3): OPENAI_API_KEY, CLAUDE_API_KEY, DEEPSEEK_API_KEY
```

The system will automatically utilize available providers and fallback dynamically if a provider is unconfigured.
