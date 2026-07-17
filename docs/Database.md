# Database Architecture - LeadForgeAI

LeadForgeAI uses **MongoDB** as its primary persistent store. The backend utilizes **Motor** (async MongoDB driver) wrapped with **Beanie ODM** (Object-Document Mapper) which uses Pydantic schemas.

## Data Models

The database maps the following primary Document collections:

### 1. Users Collection
- Mapped Document: `User`
- Indexes: `email` (unique), `created_at`

### 2. Leads Collection
- Mapped Document: `Lead`
- Indexes: `status`, `score`, `source`, `created_at`
- Vector Index: `embedding` (for semantic matching of business profiles)

### 3. Scraping Jobs
- Mapped Document: `ScrapeJob`
- Indexes: `status`, `started_at`

### 4. Campaigns
- Mapped Document: `Campaign`
- Indexes: `status`, `user_id`

---

## Seeding & Migrations

- Seeding scripts are located at [database/mongo/seed](file:///d:/Projects/LeadForgeAI/database/mongo/seed).
- Database configuration and connection setups reside in [backend/app/database/mongodb](file:///d:/Projects/LeadForgeAI/backend/app/database/mongodb).
