import axiosClient from "./axiosClient";

export interface Lead {
  id: string;
  name: string;
  website?: string;
  phone?: string;
  email?: string;
  location?: string;
  score?: number;
  status: string;
  job_id?: string;
  created_at: string;
  updated_at: string;
}

export interface LeadCreate {
  name: string;
  website?: string;
  phone?: string;
  email?: string;
  location?: string;
  score?: number;
  status?: string;
}

export interface LeadUpdate {
  name?: string;
  website?: string;
  phone?: string;
  email?: string;
  location?: string;
  score?: number;
  status?: string;
}

export interface LeadListResponse {
  items: Lead[];
  total_count: number;
  page: number;
  pages: number;
  limit: number;
}

export interface ImportResponse {
  status: string;
  message: string;
  inserted_count: number;
}

export const leadsApi = {
  getLeads: async (params: {
    page?: number;
    limit?: number;
    search?: string;
    status?: string;
    min_score?: number;
    sort_by?: string;
    sort_order?: string;
  }) => {
    const response = await axiosClient.get<LeadListResponse>("/leads", { params });
    return response.data;
  },

  getLead: async (id: string) => {
    const response = await axiosClient.get<Lead>(`/leads/${id}`);
    return response.data;
  },

  createLead: async (lead: LeadCreate) => {
    const response = await axiosClient.post<Lead>("/leads", lead);
    return response.data;
  },

  updateLead: async (id: string, lead: LeadUpdate) => {
    const response = await axiosClient.put<Lead>(`/leads/${id}`, lead);
    return response.data;
  },

  deleteLead: async (id: string) => {
    const response = await axiosClient.delete<{ status: string; message: string }>(`/leads/${id}`);
    return response.data;
  },

  importLeadsCsv: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    const response = await axiosClient.post<ImportResponse>("/leads/import", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },

  exportLeadsCsv: async (status?: string) => {
    const response = await axiosClient.get("/leads/export", {
      params: { status },
      responseType: "blob",
    });
    return response.data;
  },
};
