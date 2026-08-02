# Enterprise Resend Email & Outreach Platform — Technical Guide

This guide details the architecture, feature set, REST APIs, and UI Workspace for the upgraded **Resend Email & Outreach Platform** in LeadForgeAI.

---

## 1. Feature Specifications

| Component | Description | Implementation File |
| :--- | :--- | :--- |
| **Resend Client Adapter** | Direct REST integration using `RESEND_API_KEY` from `.env` for transactional and campaign dispatches. | [email_engine.py](file:///d:/Projects/LeadForgeAI/backend/app/email/email_engine.py) |
| **MJML & HTML Template Engine** | Compiles Jinja/Mustache tags (`{{first_name}}`, `{{company}}`) and converts MJML responsive markup to HTML. | `EmailEngine.compile_template()`, `compile_mjml()` |
| **Open & Click Tracking** | Injects 1x1 transparent tracking pixel and transforms `<a href="...">` links through click tracker. | `EmailEngine.inject_tracking()` |
| **Attachments & Inline Images** | Base64 file attachment handling for PDF, CSV, and inline images. | `EmailEngine.send_email()` |
| **Resend Webhook Processor** | Webhook listener handling `email.sent`, `email.delivered`, `email.opened`, `email.clicked`, `email.bounced`, `email.complained`. | `EmailEngine.process_resend_webhook()` |
| **Bounce & Spam Auto-Suppression** | Automatically suppresses bounced or spam-complained addresses to protect domain sender reputation. | `EmailEngine._suppressed_emails` |
| **Exponential Backoff Retry Engine** | Automatic 3-stage retry loop with $1\text{s}, 2\text{s}, 4\text{s}$ backoff for Resend 429 rate limits. | `EmailEngine.send_email()` |
| **Campaign Batch Dispatcher** | Batch outreach engine dispatching personalized emails to lead lists with scheduling & rate throttling. | `EmailEngine.launch_campaign()` |
| **Analytics Engine** | Real-time calculation of Delivery Rate %, Open Rate %, CTR %, Bounce Rate %, and Complaint Rate %. | `EmailEngine.get_analytics()` |

---

## 2. REST API Specification

All endpoints are hosted under `/api/v1/ai`:

### `POST /api/v1/ai/email/send`
- **Payload**:
  ```json
  {
    "to_email": "prospect@acme.com",
    "subject": "Invitation for {{company}}",
    "html_content": "<p>Hi {{first_name}}, demo ready!</p>",
    "variables": { "first_name": "Jordan", "company": "Acme Corp" }
  }
  ```

### `POST /api/v1/ai/email/compile-template`
- **Payload**: `{"template_str": "<mjml>...", "variables": {...}, "is_mjml": true}`
- **Description**: Compiles MJML/HTML template string into finalized HTML.

### `POST /api/v1/ai/email/campaigns`
- **Payload**:
  ```json
  {
    "name": "Q3 Lead Outreach",
    "subject": "AI Gateway for {{company}}",
    "template_html": "<p>Hi {{first_name}}...</p>",
    "recipients": [
      { "email": "alice@corp.com", "first_name": "Alice", "company": "Corp A" },
      { "email": "bob@tech.com", "first_name": "Bob", "company": "Tech B" }
    ]
  }
  ```

### `POST /api/v1/ai/email/webhooks/resend`
- **Description**: Webhook ingestion endpoint for Resend email events.

### `GET /api/v1/ai/email/analytics`
- **Description**: Returns system-wide email outreach analytics.

### `GET /api/v1/ai/email/webhooks/events`
- **Params**: `limit` (default: 50)
- **Description**: Lists recent Resend webhook telemetry events.

---

## 3. Frontend Email Workspace UI

- **URL Route**: `/email/outreach`
- **Source File**: [EmailWorkspace.tsx](file:///d:/Projects/LeadForgeAI/frontend/src/pages/email/EmailWorkspace.tsx)
- **Sections**:
  1. **Analytics Banner**: Dispatched count, Delivery Rate %, Open Rate %, Click-Through Rate (CTR) %.
  2. **Resend Email Dispatcher**: Send single transactional email with live mustache variables.
  3. **MJML Template Studio**: Responsive MJML editor with live HTML compiler preview.
  4. **Resend Webhooks Stream**: Interactive table of incoming Resend webhook events (`DELIVERED`, `OPENED`, `CLICKED`, `BOUNCED`).

---

## 4. Verification

Run the test suite:
```powershell
$env:PYTHONPATH='d:\Projects\LeadForgeAI\backend'
python scratch/test_enterprise_email_platform.py
```
