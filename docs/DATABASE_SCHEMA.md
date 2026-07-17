# Database Schema Blueprint - LeadForgeAI

This document provides schema specifications, relationships, index structures, and sample document payloads for LeadForgeAI's MongoDB database.

---

## 1. Entity-Relationship Conceptual Map

```text
  [ User ] ──(1:N)──> [ Campaign ]
      │                     │
   (1:N)                 (1:N)
      │                     │
      ▼                     ▼
[ ScrapeJob ] ──(1:N)─> [ Business (Lead) ] ──(1:1)──> [ WebsiteReport ]
```

---

## 2. Collection Specifications

### 2.1. `users` Collection
Stores credential schemas, profile settings, and membership metadata.
- **Indexes**:
  - `email`: Unique index (Fast query logins).
  - `created_at`: Basic ascending index.
- **Relationships**:
  - Has many `Campaign` records.
- **Document Example**:
```json
{
  "_id": "667be9207e0c4a17e07a3f01",
  "email": "admin@leadforge.ai",
  "password_hash": "$2b$12$R9h/CIPbshNn55GE6z1sJe9gA3D...",
  "full_name": "Debmalya Architect",
  "role": "admin",
  "is_active": true,
  "created_at": 1782384600.0
}
```

### 2.2. `businesses` (Leads) Collection
Main records containing scraped details, contact points, scores, and status.
- **Indexes**:
  - `status`: Basic lookup query optimizer.
  - `score`: Query optimizer for list filters.
  - `job_id`: Reference index.
  - `name_location`: Compound index (`{"name": 1, "location": 1}`) to prevent duplicate entries.
- **Document Example**:
```json
{
  "_id": "667be9207e0c4a17e07a3f02",
  "job_id": "667be9207e0c4a17e07a3f09",
  "name": "Chicago Premium HVAC",
  "website": "https://chicagohvac.example.com",
  "phone": "+1-312-555-0199",
  "email": "info@chicagohvac.example.com",
  "location": "Chicago, IL",
  "score": 85,
  "status": "discovered",
  "created_at": 1782384615.0
}
```

### 2.3. `website_reports` Collection
Stores detailed audit reports containing copywriting gaps and performance indicators.
- **Indexes**:
  - `business_id`: Unique reference index linking back to the business lead.
- **Document Example**:
```json
{
  "_id": "667be9207e0c4a17e07a3f03",
  "business_id": "667be9207e0c4a17e07a3f02",
  "performance_score": 62,
  "copy_gaps": ["No explicit call to action above fold", "Missing client testimonial validation"],
  "meta_tags": {
    "title": "Chicago HVAC - Heating Repair & Cooling",
    "description": "Heating repairs."
  },
  "created_at": 1782384620.0
}
```

### 2.4. `campaigns` Collection
Stores outreach campaign configurations.
- **Indexes**:
  - `user_id`: Reference index.
  - `status`: Lookup index.
- **Document Example**:
```json
{
  "_id": "667be9207e0c4a17e07a3f04",
  "user_id": "667be9207e0c4a17e07a3f01",
  "title": "HVAC Q3 Outreach Campaign",
  "status": "running",
  "template": "Hello {{name}}, we noticed some gaps on your website...",
  "created_at": 1782384625.0
}
```

### 2.5. `analytics` Collection
Maintains aggregated KPI performance metrics over time.
- **Indexes**:
  - `campaign_id_timestamp`: Compound index (`{"campaign_id": 1, "timestamp": -1}`).
- **Document Example**:
```json
{
  "_id": "667be9207e0c4a17e07a3f05",
  "campaign_id": "667be9207e0c4a17e07a3f04",
  "timestamp": 1782384630.0,
  "emails_sent": 150,
  "emails_opened": 72,
  "leads_converted": 8
}
```

### 2.6. `embeddings` (Vector Search) Collection
Stores semantic business profile vectors for retrieval matching.
- **Indexes**:
  - `business_id`: Unique reference index.
  - `vector`: 1536-dimension index for cosine distance vector search.
- **Document Example**:
```json
{
  "_id": "667be9207e0c4a17e07a3f06",
  "business_id": "667be9207e0c4a17e07a3f02",
  "embedding": [0.0123, -0.0456, 0.0892, 0.0001],
  "chunk_text": "Chicago Premium HVAC local heating repair in Chicago IL with poor call-to-actions."
}
```

### 2.7. `events` Collection
Asynchronous ledger recording all transactions and events.
- **Indexes**:
  - `name`: Basic lookup index.
  - `timestamp`: Basic chronological query index.
- **Document Example**:
```json
{
  "_id": "667be9207e0c4a17e07a3f07",
  "name": "LeadCreated",
  "payload": {
    "lead_id": "667be9207e0c4a17e07a3f02",
    "name": "Chicago Premium HVAC"
  },
  "timestamp": 1782384615.0
}
```

### 2.8. `logs` Collection
Auditing logs. Contains a TTL index to prune older logs.
- **Indexes**:
  - `timestamp`: TTL index set to expire records after 30 days (`expireAfterSeconds: 2592000`).
  - `severity`: Basic query index.
- **Document Example**:
```json
{
  "_id": "667be9207e0c4a17e07a3f08",
  "severity": "INFO",
  "module": "app.scraper.playwright",
  "message": "Crawl completed for domain: chicagohvac.example.com",
  "timestamp": 1782384620.0
}
```

### 2.9. `jobs` (ScrapeJobs) Collection
Asynchronous task executions.
- **Indexes**:
  - `status`: Lookup index.
  - `started_at`: Ascending index.
- **Document Example**:
```json
{
  "_id": "667be9207e0c4a17e07a3f09",
  "status": "completed",
  "query": "HVAC Chicago",
  "started_at": 1782384600.0,
  "completed_at": 1782384620.0
}
```

### 2.10. `settings` Collection
Global configuration profiles.
- **Indexes**:
  - `key`: Unique lookup key index.
- **Document Example**:
```json
{
  "_id": "667be9207e0c4a17e07a3f0a",
  "key": "system_maintenance",
  "value": {
    "is_enabled": false,
    "message": "Routine server updates."
  }
}
```
---

## 3. General Database Integrity Rules
- **Cascade Deletes**: If a `businesses` lead document is deleted, cascade deletion to delete its associated `website_reports` record and its `embeddings` vector.
- **TTL Enforcement**: Enforce automatic logs collection pruning via MongoDB's background pruning thread.
