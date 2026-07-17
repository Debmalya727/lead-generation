# API Specifications - LeadForgeAI

LeadForgeAI implements a RESTful JSON API using FastAPI. Authentic requests must specify JWT tokens inside request headers.

## Authentication Model

```text
Authorization: Bearer <JWT_ACCESS_TOKEN>
```

---

## Route Overview

### 1. Health Status
- **URL**: `/api/v1/health`
- **Method**: `GET`
- **Authentication**: None
- **Description**: Returns latency, system loads, and database connectivity.

### 2. Authorization
- **URL**: `/api/v1/auth/login`
  - **Method**: `POST`
  - **Payload**: JSON containing login credentials.
- **URL**: `/api/v1/auth/register`
  - **Method**: `POST`

### 3. Lead Discovery
- **URL**: `/api/v1/leads`
  - **Method**: `GET` (List leads with filters)
  - **Method**: `POST` (Submit a manual lead)
- **URL**: `/api/v1/leads/discover`
  - **Method**: `POST` (Trigger asynchronous crawling)

### 4. Website Scraping
- **URL**: `/api/v1/scraping/jobs`
  - **Method**: `GET` (List active and historic jobs)
- **URL**: `/api/v1/scraping/jobs/{id}/cancel`
  - **Method**: `POST`

### 5. Outreach Campaigns
- **URL**: `/api/v1/campaigns`
  - **Method**: `GET` / `POST`

### 6. Bookipi Invoicing
- **URL**: `/api/v1/bookipi/invoices`
  - **Method**: `POST` (Create/sync invoices)
