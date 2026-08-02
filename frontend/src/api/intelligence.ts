import axiosClient from "./axiosClient";

export interface TechStackItem {
  name: string;
  category: string;
}

export interface IntelligencePayload {
  executive_summary?: string;
  company_description?: string;
  products: string[];
  services: string[];
  industry?: string;
  company_size?: string;
  revenue_estimate?: string;
  revenue_confidence?: string;
  pain_points: string[];
  buying_signals: string[];
  ideal_sales_angle?: string;
  confidence_score?: number;
}

export interface IntelligenceStatusResponse {
  id: string;
  lead_id: string;
  company_name: string;
  website_url: string;
  status: string;
  progress: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface IntelligenceResponse extends IntelligenceStatusResponse {
  owner_id: string;
  intelligence?: IntelligencePayload;
  tech_stack: TechStackItem[];
  social_links: Record<string, string>;
  contact_page?: string;
  careers_page?: string;
  about_page?: string;
  analyzed_at?: string;
}

export const intelligenceApi = {
  startAnalysis: async (leadId: string): Promise<IntelligenceStatusResponse> => {
    const res = await axiosClient.post<IntelligenceStatusResponse>("/intelligence/analyze", {
      lead_id: leadId,
    });
    return res.data;
  },

  pollJob: async (jobId: string): Promise<IntelligenceStatusResponse> => {
    const res = await axiosClient.get<IntelligenceStatusResponse>(`/intelligence/job/${jobId}`);
    return res.data;
  },

  getByLead: async (leadId: string): Promise<IntelligenceResponse | null> => {
    try {
      const res = await axiosClient.get<IntelligenceResponse>(`/intelligence/${leadId}`);
      return res.data;
    } catch (err: any) {
      if (err.response?.status === 404) {
        return null;
      }
      throw err;
    }
  },

  deleteIntelligence: async (leadId: string): Promise<{ status: string; message: string }> => {
    const res = await axiosClient.delete(`/intelligence/${leadId}`);
    return res.data;
  },
};
