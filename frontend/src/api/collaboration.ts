import axiosClient from "./axiosClient";

export interface AgentMessageItem {
  message_id: string;
  conversation_id: string;
  job_id: string;
  task_id?: string;
  from_agent: string;
  to_agent: string;
  message_type: string;
  payload: Record<string, any>;
  confidence: number;
  status: string;
  timestamp: string;
}

export interface AgentArtifactItem {
  artifact_id: string;
  job_id: string;
  task_id?: string;
  owner_agent: string;
  artifact_type: string;
  title: string;
  metadata: Record<string, any>;
  content: Record<string, any>;
  confidence: number;
  version: number;
  parent_version_id?: string;
  created_at: string;
}

export interface ConsensusDecisionItem {
  consensus_id: string;
  job_id: string;
  task_id?: string;
  topic: string;
  proposals: Array<Record<string, any>>;
  strategy_used: string;
  resolved_output: Record<string, any>;
  winning_agent?: string;
  confidence: number;
  is_conflict: boolean;
  conflict_details?: Record<string, any>;
  resolved_at: string;
}

export interface CollaborationSummary {
  job_id: string;
  delegation_count: number;
  conflict_count: number;
  consensus_count: number;
  message_count: number;
  artifact_count: number;
  active_conversations: Array<Record<string, any>>;
  metrics_summary: Record<string, any>;
}

export interface CollaborationMetrics {
  job_id: string;
  message_count: number;
  artifact_count: number;
  consensus_count: number;
  conflict_count: number;
  delegation_count: number;
  total_sequential_latency_seconds: number;
  actual_job_latency_seconds: number;
  parallel_efficiency: number;
  agent_utilization_percent: Record<string, number>;
}

export interface DelegationPayload {
  from_agent: string;
  target_agent: string;
  task_description: string;
  inputs?: Record<string, any>;
  timeout_seconds?: number;
  max_retries?: number;
  approval_required?: boolean;
}

export const collaborationApi = {
  getMessages: async (jobId: string, params?: { conversation_id?: string; agent_id?: string }) => {
    const res = await axiosClient.get<AgentMessageItem[]>(`/agents/${jobId}/messages`, { params });
    return res.data;
  },

  postMessage: async (jobId: string, payload: { from_agent: string; to_agent: string; message_type?: string; payload?: Record<string, any>; conversation_id?: string }) => {
    const res = await axiosClient.post<AgentMessageItem>(`/agents/${jobId}/message`, payload);
    return res.data;
  },

  getArtifacts: async (jobId: string, params?: { artifact_type?: string; owner_agent?: string }) => {
    const res = await axiosClient.get<AgentArtifactItem[]>(`/agents/${jobId}/artifacts`, { params });
    return res.data;
  },

  getConsensus: async (jobId: string) => {
    const res = await axiosClient.get<ConsensusDecisionItem[]>(`/agents/${jobId}/consensus`);
    return res.data;
  },

  getSummary: async (jobId: string) => {
    const res = await axiosClient.get<CollaborationSummary>(`/agents/${jobId}/collaboration`);
    return res.data;
  },

  getMetrics: async (jobId: string) => {
    const res = await axiosClient.get<CollaborationMetrics>(`/agents/${jobId}/metrics`);
    return res.data;
  },

  delegateTask: async (jobId: string, payload: DelegationPayload) => {
    const res = await axiosClient.post(`/agents/${jobId}/delegate`, payload);
    return res.data;
  },

  connectStream: (jobId: string, onEvent: (event: any) => void) => {
    const token = localStorage.getItem("access_token");
    const url = `/api/v1/agents/${jobId}/stream${token ? `?token=${token}` : ""}`;
    const es = new EventSource(url);
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        onEvent(data);
      } catch {}
    };
    return () => es.close();
  },
};
