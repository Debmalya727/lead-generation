import axiosClient from "./axiosClient";

export interface ScheduledJob {
  job_id: string;
  name: string;
  description: string;
  workflow_template_id: string;
  cron_expression?: string;
  interval_seconds?: number;
  priority: string;
  is_active: boolean;
  last_run_at?: string;
  next_run_at?: string;
  run_count: number;
}

export interface JobHistory {
  history_id: string;
  job_id: string;
  workflow_execution_id?: string;
  status: string;
  duration_ms: number;
  started_at: string;
}

export const schedulerApi = {
  listJobs: async () => {
    const res = await axiosClient.get<ScheduledJob[]>("/scheduler/jobs");
    return res.data;
  },

  createJob: async (payload: { name: string; workflow_template_id: string; cron_expression?: string; priority?: string; description?: string }) => {
    const res = await axiosClient.post<ScheduledJob>("/scheduler/jobs", payload);
    return res.data;
  },

  runJobNow: async (jobId: string) => {
    const res = await axiosClient.post<{ status: string; execution_id: string; history: JobHistory }>(`/scheduler/job/${jobId}/run`);
    return res.data;
  },

  getHistory: async (jobId: string) => {
    const res = await axiosClient.get<JobHistory[]>(`/scheduler/job/${jobId}/history`);
    return res.data;
  },
};
