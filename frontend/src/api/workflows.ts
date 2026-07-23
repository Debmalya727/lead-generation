import axiosClient from "./axiosClient";

export interface WorkflowExecutionItem {
  execution_id: string;
  workflow_id: string;
  job_id?: string;
  lead_id?: string;
  company_name?: string;
  status: string;
  progress: number;
  current_step_id?: string;
  execution_stats: Record<string, any>;
  context_data: Record<string, any>;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface WorkflowStepItem {
  step_execution_id: string;
  execution_id: string;
  step_id: string;
  name: string;
  step_type: string;
  target: string;
  status: string;
  inputs: Record<string, any>;
  outputs: Record<string, any>;
  execution_time_seconds: number;
  retry_count: number;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
}

export interface WorkflowCheckpointItem {
  checkpoint_id: string;
  execution_id: string;
  step_id: string;
  state_snapshot: Record<string, any>;
  completed_step_ids: string[];
  pending_step_ids: string[];
  reason: string;
  created_at: string;
}

export interface ToolItem {
  tool_id: string;
  name: string;
  description: string;
  category: string;
  version: string;
  input_schema: Record<string, any>;
  output_schema: Record<string, any>;
  permissions: string[];
  timeout: number;
  cost_estimate: number;
}

export const workflowsApi = {
  runWorkflow: async (payload: { workflow_id: string; company_name?: string; lead_id?: string; inputs?: Record<string, any>; policy_id?: string }) => {
    const res = await axiosClient.post<WorkflowExecutionItem>("/workflows/run", payload);
    return res.data;
  },

  listWorkflows: async (params?: { status?: string; limit?: number; skip?: number }) => {
    const res = await axiosClient.get<{ total_count: number; items: WorkflowExecutionItem[] }>("/workflows", { params });
    return res.data;
  },

  getWorkflowExecution: async (id: string) => {
    const res = await axiosClient.get<WorkflowExecutionItem>(`/workflows/${id}`);
    return res.data;
  },

  getWorkflowSteps: async (id: string) => {
    const res = await axiosClient.get<WorkflowStepItem[]>(`/workflows/${id}/steps`);
    return res.data;
  },

  getWorkflowCheckpoints: async (id: string) => {
    const res = await axiosClient.get<WorkflowCheckpointItem[]>(`/workflows/${id}/checkpoints`);
    return res.data;
  },

  listTools: async () => {
    const res = await axiosClient.get<ToolItem[]>("/tools");
    return res.data;
  },

  getTool: async (toolId: string) => {
    const res = await axiosClient.get<ToolItem>(`/tools/${toolId}`);
    return res.data;
  },

  executeTool: async (toolId: string, payload: { inputs?: Record<string, any>; invoker_agent?: string }) => {
    const res = await axiosClient.post(`/tools/${toolId}/execute`, payload);
    return res.data;
  },

  cancelWorkflow: async (id: string) => {
    const res = await axiosClient.post<WorkflowExecutionItem>(`/workflows/${id}/cancel`);
    return res.data;
  },

  resumeWorkflow: async (id: string) => {
    const res = await axiosClient.post<WorkflowExecutionItem>(`/workflows/${id}/resume`);
    return res.data;
  },
};
