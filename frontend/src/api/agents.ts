import axiosClient from "./axiosClient";

export interface ExecutionTask {
  task_id: string;
  name: string;
  agent_name: string;
  description: string;
  dependencies: string[];
  priority: number;
  retry_count: number;
  max_retries: number;
  timeout_seconds: number;
  parallelizable: boolean;
  approval_required: boolean;
  status: string;
  inputs: Record<string, any>;
  outputs: Record<string, any>;
  error_message?: string;
  execution_time_seconds: number;
  started_at?: string;
  completed_at?: string;
}

export interface ExecutionPlan {
  plan_id: string;
  goal: string;
  tasks: ExecutionTask[];
  task_graph_json: {
    nodes: Array<{ id: string; label: string; agent: string; status: string; priority?: number }>;
    edges: Array<{ source: string; target: string }>;
    pipeline_type?: string;
  };
  created_at: string;
}

export interface AgentJob {
  job_id: string;
  goal: string;
  lead_id?: string;
  owner_id: string;
  status: string;
  progress: number;
  plan?: ExecutionPlan;
  current_task_id?: string;
  execution_stats: Record<string, any>;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface AgentJobListResponse {
  total_count: number;
  items: AgentJob[];
}

export interface AgentEvent {
  event_id: string;
  job_id: string;
  event_type: string;
  source_agent: string;
  task_id?: string;
  payload: Record<string, any>;
  timestamp: string;
}

export interface AgentRegistryItem {
  agent_id: string;
  name: string;
  version: string;
  description: string;
  capabilities: string[];
}

export interface ExecutiveReport {
  report_id: string;
  job_id: string;
  lead_id?: string;
  owner_id: string;
  goal: string;
  company_name: string;
  executive_summary: string;
  opportunity_score: number;
  sales_playbook: Record<string, any>;
  top_pain_points: string[];
  winning_value_proposition: string;
  key_differentiators: string[];
  risk_assessment: Array<{ risk: string; severity: string; mitigation: string }>;
  recommended_actions: Array<{ action: string; priority: string; timeline: string; owner: string }>;
  execution_checklist: Array<{ task: string; due: string; status: string }>;
  best_outreach_channel: string;
  estimated_deal_size: string;
  estimated_close_timeline: string;
  overall_confidence: number;
  data_quality_notes: string;
  research_section: Record<string, any>;
  memory_section: Record<string, any>;
  strategy_section: Record<string, any>;
  outreach_section: Record<string, any>;
  review_section: Record<string, any>;
  created_at: string;
}

export interface AgentRunParams {
  goal: string;
  lead_id?: string;
  execution_mode?: "auto" | "business_pipeline" | "custom";
  company_name?: string;
  approval_required?: boolean;
}

export const agentsApi = {
  submitJob: async (params: AgentRunParams) => {
    const response = await axiosClient.post<AgentJob>("/agents/run", params);
    return response.data;
  },

  listJobs: async (params?: { status?: string; lead_id?: string; limit?: number; skip?: number }) => {
    const response = await axiosClient.get<AgentJobListResponse>("/agents/jobs", { params });
    return response.data;
  },

  getJob: async (jobId: string) => {
    const response = await axiosClient.get<AgentJob>(`/agents/${jobId}`);
    return response.data;
  },

  getEvents: async (jobId: string) => {
    const response = await axiosClient.get<AgentEvent[]>(`/agents/${jobId}/events`);
    return response.data;
  },

  getGraph: async (jobId: string) => {
    const response = await axiosClient.get(`/agents/${jobId}/graph`);
    return response.data;
  },

  cancelJob: async (jobId: string) => {
    const response = await axiosClient.post<AgentJob>(`/agents/${jobId}/cancel`);
    return response.data;
  },

  retryJob: async (jobId: string) => {
    const response = await axiosClient.post<AgentJob>(`/agents/${jobId}/retry`);
    return response.data;
  },

  approveTask: async (jobId: string, taskId: string) => {
    const response = await axiosClient.post<AgentJob>(`/agents/${jobId}/approve`, { task_id: taskId });
    return response.data;
  },

  getReport: async (jobId: string) => {
    const response = await axiosClient.get<ExecutiveReport>(`/agents/${jobId}/report`);
    return response.data;
  },

  listRegisteredAgents: async () => {
    const response = await axiosClient.get<AgentRegistryItem[]>("/agents/registry/agents");
    return response.data;
  },
};
