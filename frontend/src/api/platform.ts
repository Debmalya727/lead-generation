import axiosClient from "./axiosClient";

export interface HealthStatus {
  status: string;
  timestamp: number;
  latency_ms: number;
  services: {
    api: string;
    database: string;
    cache: string;
    celery_workers: string;
    gateway: string;
  };
}

export interface SystemMetrics {
  workflow_duration_ms_avg: number;
  workflow_success_count: number;
  workflow_failure_count: number;
  tool_duration_ms_avg: number;
  tool_failure_count: number;
  agent_duration_ms_avg: number;
  average_planning_time_ms: number;
  conversation_latency_ms: number;
  memory_usage_mb: number;
  cpu_utilization_pct: number;
  gpu_utilization_pct: number;
  queue_length: number;
}

export interface FeatureFlag {
  flag_key: string;
  name: string;
  description: string;
  is_enabled: boolean;
  environment?: string;
}

export interface AuditLog {
  audit_id: string;
  event_type: string;
  actor_id: string;
  correlation_id?: string;
  resource_type: string;
  resource_id?: string;
  details: Record<string, any>;
  status: string;
  timestamp: string;
}

export interface RequestTrace {
  trace_id: string;
  span_id: string;
  name: string;
  component: string;
  duration_ms: number;
  status: string;
  attributes: Record<string, any>;
  timestamp: string;
}

export const platformApi = {
  getHealth: async () => {
    const res = await axiosClient.get<HealthStatus>("/health");
    return res.data;
  },

  getMetrics: async () => {
    const res = await axiosClient.get<SystemMetrics>("/metrics");
    return res.data;
  },

  getSystemInfo: async () => {
    const res = await axiosClient.get<Record<string, any>>("/system");
    return res.data;
  },

  listAuditLogs: async (params?: { event_type?: string; limit?: number; skip?: number }) => {
    const res = await axiosClient.get<{ total_count: number; items: AuditLog[] }>("/platform/audit-logs", { params });
    return res.data;
  },

  listFeatureFlags: async () => {
    const res = await axiosClient.get<FeatureFlag[]>("/platform/feature-flags");
    return res.data;
  },

  setFeatureFlag: async (payload: { flag_key: string; is_enabled: boolean; name?: string }) => {
    const res = await axiosClient.post<FeatureFlag>("/platform/feature-flags", payload);
    return res.data;
  },

  listTraces: async (params?: { trace_id?: string; limit?: number; skip?: number }) => {
    const res = await axiosClient.get<{ total_count: number; items: RequestTrace[] }>("/platform/traces", { params });
    return res.data;
  },
};
