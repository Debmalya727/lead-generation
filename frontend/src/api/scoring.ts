import axiosClient from "./axiosClient";

export interface ScoreBreakdown {
  feature: string;
  label: string;
  score: number;
  max_score: number;
  rationale: string;
}

export interface ScoringStatusResponse {
  id: string;
  lead_id: string;
  company_name: string;
  status: string;
  progress: number;
  score: number | null;
  priority: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface ScoringResponse {
  id: string;
  lead_id: string;
  owner_id: string;
  company_name: string;
  website_url: string | null;
  status: string;
  progress: number;
  error_message: string | null;
  score: number | null;
  priority: string | null;
  rule_score: number | null;
  llm_score_adjustment: number;
  score_breakdown: ScoreBreakdown[];
  strengths: string[];
  weaknesses: string[];
  risk_factors: string[];
  recommended_outreach: string | null;
  score_explanation: string | null;
  confidence_score: number | null;
  scoring_version: string;
  scoring_profile: string;
  created_at: string;
  updated_at: string;
  scored_at: string | null;
}

export const scoringApi = {
  startScoring: async (leadId: string): Promise<ScoringStatusResponse> => {
    const res = await axiosClient.post("/scoring/analyze", { lead_id: leadId });
    return res.data;
  },

  pollJob: async (jobId: string): Promise<ScoringStatusResponse> => {
    const res = await axiosClient.get(`/scoring/job/${jobId}`);
    return res.data;
  },

  getByLead: async (leadId: string): Promise<ScoringResponse> => {
    const res = await axiosClient.get(`/scoring/${leadId}`);
    return res.data;
  },

  deleteScore: async (leadId: string): Promise<void> => {
    await axiosClient.delete(`/scoring/${leadId}`);
  },
};
