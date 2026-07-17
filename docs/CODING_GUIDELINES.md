# Coding Guidelines - LeadForgeAI

This document outlines the coding standards, layer rules, patterns, and style guide for LeadForgeAI to ensure high scalability and structure across modules.

---

## 1. Architectural Layers & Boundary Rules

LeadForgeAI enforces a strict **layered dependency rule**. Higher-level layers can query lower-level layers, but lower-level layers must **never** reference higher-level layers.

```text
  [ Client Request ]
         ↓
+------------------+
|    API Layer     |  <-- backend/app/api/
+------------------+
         ↓
+------------------+
|   Module Layer   |  <-- backend/app/modules/
+------------------+
         ↓
+------------------+
|   Engine Layer   |  <-- backend/app/engine/
+------------------+
         ↓
+------------------+
|  Services Layer  |  <-- backend/app/services/ & backend/app/integrations/
+------------------+
         ↓
+------------------+
| Repository Layer |  <-- backend/app/database/mongodb/repositories/
+------------------+
         ↓
  [ MongoDB Database ]
```

### 🚫 Prohibited Cross-Layer Access (Crucial Rules)

1. **No Direct Database Access in Controllers**: The API layer (`app/api/`) must **never** import or query document models or repositories directly.
   - ❌ **Incorrect**: `await LeadDocument.find_all().to_list()` in a controller.
   -  **Correct**: The controller calls `LeadFinderModule.get_active_leads()`, which queries the repository.
2. **No Business Logic in Database Schemas**: MongoDB models (Beanie Documents) represent raw data structure and relationships. They must **never** contain orchestration logic, scraping methods, or integrations.
3. **Third-Party Anti-Corruption**: Services must never expose raw API responses from partners (like Bookipi or OpenRouter). Instead, integrate using adapters inside `app/integrations/` that translate partner structures to internal Pydantic schemas.

---

## 2. Code Organization & Patterns

### 2.1. Dependency Injection
Use FastAPI's `Depends` for all controllers and modules dependency references to support automated testing and stub mocking.

```python
# Correct DI pattern
@router.get("/{lead_id}", response_model=LeadResponseSchema)
async def get_lead(
    lead_id: str,
    lead_module: LeadFinderModule = Depends(get_lead_finder_module)
):
    return await lead_module.retrieve_lead(lead_id)
```

### 2.2. Schema Layer Separation
Keep validation schemas distinct from Beanie documents.
- **Request Schemas**: Custom validation patterns (e.g. `LeadCreateRequest`).
- **Response Schemas**: Standard HTTP outputs sanitizing sensitive database records (e.g. `UserResponse`).
- **Database Models**: Pure Beanie document entities inheriting `beanie.Document`.

---

## 3. Style Guide & File Naming Conventions

### 3.1. Python Code
- **Formatting**: Strictly follow `black` and `isort` configurations.
- **Naming**:
  - Folders and Python files: `snake_case` (e.g., `lead_pipeline/`, `lead_scorer.py`).
  - Classes: `PascalCase` (e.g., `LeadFinderModule`, `DatabaseManager`).
  - Functions & Variables: `snake_case` (e.g., `calculate_lead_score()`).
  - Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRY_LIMIT`).

### 3.2. TypeScript & React
- **Filenames**:
  - React components & layouts: `PascalCase` (e.g., `LeadDashboard.tsx`, `GlassCard.tsx`).
  - Hooks, services, and utils: `camelCase` (e.g., `useLenis.ts`, `apiService.ts`).
  - Style themes: `camelCase` or `kebab-case` (e.g., `persianTheme.ts`).
- **Path Mapping**: Always use alias absolute paths:
  - ❌ `import Button from '../../../../components/common/Button'`
  -  `import { Button } from '@/components/common/Button'`
