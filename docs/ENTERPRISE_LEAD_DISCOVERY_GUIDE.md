# LeadForgeAI — Enterprise Lead Discovery Platform Guide

## 1. Executive Summary & Overview
The LeadForgeAI Enterprise Lead Discovery Platform provides an end-to-end multi-provider business discovery, normalization, AI deduplication, AI enrichment, quality scoring, and CRM ingestion engine. It enables discovering verified, high-intent B2B business leads across major commercial directories in India and worldwide:
1. **Google Maps (Google Places API v1 / Playwright Scraper Fallback)**
2. **Justdial (Playwright Directory & Search Page Extractor)**
3. **IndiaMART (Playwright Supplier & GSTIN Extractor)**
4. **TradeIndia (Playwright Seller & Direct Contact Extractor)**

---

## 2. 9-Stage Async Lead Discovery Pipeline
Every discovery request runs through an automated, resilient 9-stage asynchronous pipeline orchestrated via Celery and asyncio:

```
[Stage 1: Job Initialization & Validation]
                  │
[Stage 2: Multithreaded Multi-Provider Search] (Google Maps + Justdial + IndiaMART + TradeIndia)
                  │
[Stage 3: Canonical Lead Normalization Engine] (E.164 Phones, Domain, GSTIN, Title Casing, Fingerprinting)
                  │
[Stage 4: AI Cross-Provider Deduplication] (GSTIN Match, Domain Match, Phone Match, String Distance)
                  │
[Stage 5: AI Lead Enrichment & Web Intelligence] (AIGateway Executive Summary, Tech Stack, Intent, Maturity)
                  │
[Stage 6: Multi-Component Lead Quality Scoring] (Hot >= 70, Warm >= 40, Cold < 40)
                  │
[Stage 7: Knowledge Fabric Ingestion & Persistence] (Knowledge Object Ingestion via Gateway)
                  │
[Stage 8: Event Bus Broadcast & Real-time Telemetry] (LeadDiscovered & LeadCRMCreated events)
                  │
[Stage 9: Daily Analytics Snapshot & Dashboard Metrics]
```

---

## 3. Core Component Architecture

### A. Provider Circuit Breakers & Resilience (`app.modules.discovery.providers.circuit_breaker`)
- Automatically monitors provider failure rates.
- Opens circuit when consecutive errors exceed threshold (5 failures), protecting external APIs and preventing cascading timeouts.
- Automatically transitions to `HALF-OPEN` after reset timeout (60 seconds) to test provider recovery.

### B. Dynamic Provider Registry (`app.modules.discovery.providers.provider_registry`)
- Centralized singleton registry auto-discovers and registers provider instances.
- Allows dynamically querying provider health (`/api/v1/discovery/providers`) and filtering available search capabilities without code changes.

### C. Lead Normalization Engine (`app.modules.discovery.normalization.lead_normalizer`)
- E.164 international phone formatting (`+919876543210`).
- Business name title casing and legal entity normalization (`Pvt Ltd`, `Co.`, `LLP`).
- Domain extraction (`acme.com` from `https://www.acme.com/about`).
- 15-character GSTIN regex validation (`27ABCDE1234F1Z5`).
- Unique fingerprint generation (`fp_gst_27ABCDE1234F1Z5`, `fp_dom_acme_acme.com`).

### D. AI Deduplication Engine (`app.modules.discovery.deduplication.deduplication_engine`)
- Merges multi-source duplicate records into unified canonical lead profiles.
- Computes confidence scores (1.0 for GSTIN/Domain match, 0.9 for Phone match, 0.85 for string similarity).
- Stores complete audit trails in `DuplicateMergeLogDocument`.

### E. AI Lead Enrichment Engine (`app.modules.discovery.enrichment.enrichment_engine`)
- Integrates with `AIGateway` (`gemini-1.5-flash`) for executive B2B summaries, buyer intent estimation (`High`/`Medium`/`Low`), and industry classification.
- Conducts web intelligence detection for CMS (`WordPress`/`Shopify`), ecommerce platforms, analytics tags, and verified social media handles.

### F. Multi-Component Quality Scoring (`app.modules.discovery.scoring.quality_scorer`)
Assigns a 0–100 quality score based on 7 weighted signals:
1. **Website Quality (20 pts)**: Active domain, SSL security, custom domain.
2. **Contact Completeness (20 pts)**: E.164 phone, valid email address, physical address.
3. **Review & Social Proof (15 pts)**: Rating >= 4.0, review count >= 10.
4. **Business Maturity (15 pts)**: Established enterprise vs small business.
5. **Social Media Activity (10 pts)**: Verified LinkedIn, Facebook, Twitter profiles.
6. **Tech Stack Signals (10 pts)**: Modern web technologies detected.
7. **AI Intent Confidence (10 pts)**: AI buyer intent rating.

Quality Tiers:
- **Hot Lead**: Total Score &ge; 70
- **Warm Lead**: Total Score &ge; 40 and &lt; 70
- **Cold Lead**: Total Score &lt; 40

---

## 4. REST API Endpoints (`/api/v1/discovery`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/discovery/search` | Trigger new multi-provider discovery pipeline job |
| `GET` | `/api/v1/discovery/job/{job_id}` | Get real-time job status, progress percentage, and stage |
| `GET` | `/api/v1/discovery/results/{job_id}` | Fetch enriched discovered leads for a job |
| `GET` | `/api/v1/discovery/duplicates/{job_id}` | Fetch AI deduplication merge audit logs for a job |
| `POST` | `/api/v1/discovery/save-leads` | Import selected discovered leads into CRM |
| `GET` | `/api/v1/discovery/providers` | Get health and circuit breaker status for all providers |
| `GET` | `/api/v1/discovery/analytics/dashboard` | Get discovery platform metrics, dedup rates, and quality breakdown |

---

## 5. UI Workspace Overview (`EnterpriseDiscoveryWorkspace.tsx`)
The React Discovery Workspace provides:
- **Multi-Provider Toggles**: Interactive checkboxes for Google Maps, Justdial, IndiaMART, and TradeIndia.
- **Real-Time Progress Gauge**: Live 9-stage pipeline progress bar with status percentage.
- **Interactive Lead Cards**: Quality tier badges (Hot/Warm/Cold), quality scores, tech stack pills, and AI summaries.
- **AI Deduplication Viewer**: Full transparency into merged duplicate clusters, confidence scores, and match reasons.
- **CRM Ingestion**: Multi-select leads with single-click import into LeadForgeAI CRM database.
