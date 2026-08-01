import axiosClient from "./axiosClient";

export interface DiscoveredLead {
  id: string;
  name: string;
  website?: string;
  phone?: string;
  email?: string;
  location?: string;
  score?: number;
  provider: string;
}

export interface JobStatusResponse {
  id: string;
  keyword: string;
  location: string;
  providers: string[];
  status: string;
  progress: number;
  total_results: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface SaveLeadsResponse {
  status: string;
  message: string;
  saved_count: number;
  skipped_count: number;
}

export const discoveryApi = {
  startDiscovery: async (payload: { keyword: string; location: string; providers: string[]; website_filter: string; limit?: number }) => {
    const response = await axiosClient.post<JobStatusResponse>("/discovery/start", payload);
    return response.data;
  },

  getJobStatus: async (jobId: string) => {
    const response = await axiosClient.get<JobStatusResponse>(`/discovery/${jobId}`);
    return response.data;
  },

  getJobResults: async (jobId: string) => {
    const response = await axiosClient.get<DiscoveredLead[]>(`/discovery/results/${jobId}`);
    return response.data;
  },

  cancelJob: async (jobId: string) => {
    const response = await axiosClient.post<{ status: string; message: string }>(`/discovery/cancel/${jobId}`);
    return response.data;
  },

  saveLeads: async (jobId: string, leadIds: string[]) => {
    const response = await axiosClient.post<SaveLeadsResponse>(`/discovery/results/${jobId}/save`, {
      lead_ids: leadIds,
    });
    return response.data;
  },
};
