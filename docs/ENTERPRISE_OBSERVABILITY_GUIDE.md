# Enterprise AI Observability Platform — Technical Guide

This guide details the architecture, feature set, REST APIs, and UI Workspace for the **Enterprise AI Observability Platform** in LeadForgeAI.

---

## 1. Feature Specifications

| Component | Description | Implementation File |
| :--- | :--- | :--- |
| **OpenTelemetry Distributed Tracing** | Context manager creating trace IDs, span IDs, and parent spans across gateway, tools, and agents. | [observability.py](file:///d:/Projects/LeadForgeAI/backend/app/ai/observability/observability.py) |
| **Prometheus Exporter** | Standard Prometheus metric format (`/metrics` endpoint) for scrapers. | `ObservabilityEngine.export_prometheus_metrics()` |
| **Structured Correlation Logging** | Contextual JSON logging attaching `correlation_id` and `request_id` to log entries. | `ObservabilityEngine.finish_trace()` |
| **Statistical Anomaly Detection** | Real-time Z-score latency spike detection flagging requests exceeding $\mu + 2\sigma$. | `ObservabilityEngine.check_anomaly_and_sla()` |
| **SLA Compliance Monitoring** | Real-time calculation of Uptime % ($99.5\%$ target) and P95 latency thresholds ($< 2000\text{ms}$). | `ObservabilityEngine.get_sla_uptime_percent()` |
| **Alert Dispatcher** | Alert event manager firing Slack, Email, Webhook receivers on SLA breaches or budget overruns. | `ObservabilityEngine.dispatch_alert()` |

---

## 2. REST API Specification

All endpoints are hosted under `/api/v1/ai`:

### `GET /api/v1/ai/metrics` (Response format: `text/plain`)
- **Description**: Standard Prometheus metric text output for Prometheus/Grafana collection.

### `GET /api/v1/ai/observability/overview`
- **Description**: Returns system SLA compliance score, P95 latency, total request count, total cost USD, and active alert count.

### `GET /api/v1/ai/observability/traces`
- **Params**: `limit` (default: 50)
- **Description**: Returns recent distributed request traces with OpenTelemetry spans.

### `GET /api/v1/ai/observability/alerts`
- **Params**: `limit` (default: 50)
- **Description**: Returns active and historical telemetry alerts (SLA breach, latency anomaly, budget overrun).

### `POST /api/v1/ai/observability/alerts/trigger`
- **Payload**:
  ```json
  {
    "alert_type": "LATENCY_ANOMALY",
    "severity": "WARNING",
    "source_component": "AI Gateway Provider Adapter",
    "message": "High latency spike detected on Gemini Flash route."
  }
  ```

---

## 3. Frontend Observability Workspace UI

- **URL Route**: `/ai/observability`
- **Source File**: [ObservabilityWorkspace.tsx](file:///d:/Projects/LeadForgeAI/frontend/src/pages/ai/ObservabilityWorkspace.tsx)
- **Sections**:
  1. **Metrics Overview Banner**: System SLA Compliance Score %, P95 Latency ms, Total Requests, and Active Alert Count.
  2. **Prometheus Exporter Viewer**: Real-time `/metrics` preview panel.
  3. **OpenTelemetry Distributed Traces Table**: Interactive trace viewer showing correlation IDs, endpoints, latency ms, and status codes.
  4. **Telemetry Alerts Feed & Manual Dispatcher**: Active alerts list and test alert event dispatcher.

---

## 4. Verification

Run the test suite:
```powershell
$env:PYTHONPATH='d:\Projects\LeadForgeAI\backend'
python scratch/test_enterprise_observability.py
```
