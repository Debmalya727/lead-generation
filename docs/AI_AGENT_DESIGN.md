# AI Agent Design Specifications - LeadForgeAI

This document provides detailed design specifications for all autonomous AI agents in the LeadForgeAI platform.

---

## 1. Agent Coordination Graph

Our agent ecosystem communicates asynchronously, passing state payload contexts from planning steps through outreach compilation.

```text
+-------------------+
|   Manager Agent   |  <-- High level query coordinator
+-------------------+
         ↓
+-------------------+
|   Planner Agent   |  <-- Goal breakdown & tool scheduler
+-------------------+
         ↓
+-------------------+
|   Scraper Agent   |  <-- Business directories crawling
+-------------------+
         ↓
+-------------------+
|  Research Agent   |  <-- Contacts & site crawler
+-------------------+
         ↓
+-------------------+
| Website Analyzer  |  <-- Gaps and copy grader
+-------------------+
         ↓
+-------------------+
|    Lead Scorer    |  <-- Target suitability matrix
+-------------------+
         ↓
+-----------------------------+
| Outreach & Bookipi Agents   |  <-- Copywriting and billing dispatch
+-----------------------------+
```

---

## 2. Detailed Agent Specifications

### 2.1. Manager Agent (`app/agents/manager`)
- **Responsibilities**: Receives user leads request queries (e.g. *"Discover and audit HVAC services in Chicago"*), triggers planners, coordinates progress loops, and updates UI status.
- **Inputs**: User search parameter query, location targets, budget constraints.
- **Outputs**: Job execution schema matching scraper targets and lists of desired outcomes.
- **Memory**: Persistent workspace session logs database.
- **Tools**: Job database trigger functions, workflow scheduler connectors.
- **System Prompt**: *"You are the LeadForgeAI Orchestration Supervisor. Your goal is to coordinate search criteria, delegate tasks to specialized planner and researcher agents, and aggregate results."*

### 2.2. Research Agent (`app/agents/researcher`)
- **Responsibilities**: Enriches basic lead records by crawling websites and social profiles for missing contacts, emails, and technologies.
- **Inputs**: Company name, domain name URL, raw home page text.
- **Outputs**: JSON contact card (verified email addresses, LinkedIn handles, phone numbers, and web technologies found).
- **Memory**: Conversation memory cache and database collection lookups.
- **Tools**: HTTP crawler, email extraction parser, social profile lookup finder.
- **System Prompt**: *"You are the LeadForgeAI Context Enrichment Researcher. Your goal is to scan web assets and extract key contacts, emails, and tech stacks."*

### 2.3. Scraper Agent (`app/agents/scraper`)
- **Responsibilities**: Automates local directory scanning to populate primary lead lists.
- **Inputs**: Location boundaries, business category keywords.
- **Outputs**: Array of target objects (business name, telephone, raw address, website URL).
- **Memory**: Visited URL cache (stores hashes of URLs to avoid duplicate scraping in the current run).
- **Tools**: Google Maps scraper client, Justdial parser client.
- **System Prompt**: *"You are the LeadForgeAI Crawler Scraper. Your task is to query local business directories for target keywords and location ranges."*

### 2.4. Website Analyzer (`app/agents/website_analyzer`)
- **Responsibilities**: Conducts site reviews, auditing performance, mobile friendliness, messaging gaps, and call-to-action effectiveness.
- **Inputs**: Crawled HTML structure, screenshots storage links.
- **Outputs**: Detailed site audit JSON report card (mobile score, call-to-action count, copywriting gaps, improvement suggestions).
- **Memory**: Structured template checklist memory.
- **Tools**: HTML parsing tool, lighthouse metrics mock api tool.
- **System Prompt**: *"You are the LeadForgeAI Website Auditor. Grade the target's copywriting clarity, contact avenues, and conversion funnels."*

### 2.5. Lead Scorer (`app/agents/lead_scorer`)
- **Responsibilities**: Evaluates prospects based on business criteria and audits to calculate a qualification rank.
- **Inputs**: Lead contacts data, website analyzer audit cards, user search target criteria.
- **Outputs**: Composite score (0-100), classification level ("Hot", "Warm", "Cold"), matching criteria details.
- **Memory**: Vector database search templates lookup (historical matching feedback).
- **Tools**: Cosine similarity calculators, target criteria matching validation engine.
- **System Prompt**: *"You are the LeadForgeAI Lead Scorer. Evaluate the target lead based on matching requirements and business revenue parameters."*

### 2.6. Bookipi Agent (`app/agents/bookipi_engine`)
- **Responsibilities**: Automates partner invoice creation, synching billing tokens, and dispatching payment reminders.
- **Inputs**: Scored leads list, outreach campaign goals, partner billing tokens.
- **Outputs**: Synchronized Bookipi invoice schemas.
- **Memory**: Database transaction ledger.
- **Tools**: Bookipi API integration adapter hooks.
- **System Prompt**: *"You are the Bookipi Invoicing Agent. Synchronize transaction logs and create invoices for outreach leads."*

### 2.7. Outreach Agent (`app/agents/outreach`)
- **Responsibilities**: Drafts hyper-personalized outreach campaigns referencing the gaps found by the website analyzer.
- **Inputs**: Lead contacts data, website audit reports, campaign copy templates.
- **Outputs**: Draft sales letter (subject line, body copy, custom landing page link) for email or LinkedIn messages.
- **Memory**: History of successful conversions vector cache.
- **Tools**: Prompt template interpolator, Resend dispatcher client.
- **System Prompt**: *"You are the LeadForgeAI Outreach Copywriter. Craft compelling, personalized outreach messages referencing the target's specific website gaps."*

---

## 3. Multi-Agent LLM Routing Architecture

The lead discovery & analysis pipeline routes agent tasks across specialized LLM models and providers to maximize reasoning power, execution speed, and cost efficiency:

| Agent | Provider | Model | Why / Role |
| --- | --- | --- | --- |
| 🧠 **Manager** | OpenRouter | **NVIDIA Nemotron 3 Ultra (free)** | Strong reasoning & high-level multi-agent orchestration |
| 📋 **Planner** | Groq | **GPT-OSS 20B** | Ultra-fast DAG planning & tool call decision routing |
| 🕷️ **Scraper** | Ollama | **Qwen3 4B/8B** | Local + free, structured lead directory extraction |
| 🔎 **Research** | Groq | **Llama 3.3 70B** | Deep context enrichment, decision-maker & buying signal reasoning |
| 🌐 **Website Analyzer** | Ollama / HF | **Gemma 3 12B** | Content analysis, vision-capable landing page & conversion gap audit |
| 🛟 **Fallback** | OpenRouter | **openrouter/free** | Automatic failover routing to active free models when primary APIs fail |

---

