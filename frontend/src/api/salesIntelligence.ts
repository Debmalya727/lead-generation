import axiosClient from './axiosClient';

export interface DecisionMaker {
  name: string;
  designation: string;
  department: string;
  linkedin_url?: string;
  company_email?: string;
  personal_email?: string;
  phone?: string;
  confidence_score: number;
  source: string;
  discovery_timestamp?: string;
}

export interface GrowthSignal {
  type: string;
  description: string;
  confidence: number;
  source: string;
  date?: string;
}

export interface Milestone {
  year_or_date: string;
  event: string;
  category: string;
}

export interface CompanyTimeline {
  founded_year?: string;
  expansion_history: string[];
  funding_history: string[];
  milestones: Milestone[];
  current_stage: string;
  future_direction?: string;
  recent_events: string[];
  ai_summary?: string;
}

export interface SalesOpportunityClassification {
  categories: string[];
  primary_category: string;
  rationale?: string;
}

export interface SalesGraphNode {
  id: string;
  label: string;
  type: string;
}

export interface SalesGraphEdge {
  source_id: string;
  target_id: string;
  relation_type: string;
  weight: number;
}

export interface RelationshipGraph {
  nodes: SalesGraphNode[];
  edges: SalesGraphEdge[];
}

export interface SalesRecommendation {
  best_contact_person?: string;
  best_outreach_channel: string;
  best_time_to_contact: string;
  pain_points: string[];
  recommended_product_pitch?: string;
  conversation_starter?: string;
  recommended_email_tone: string;
  risk_factors: string[];
  opportunity_summary?: string;
  competitive_advantage?: string;
  objections: string[];
  followup_strategy?: string;
}

export interface SalesIntelligenceStatusResponse {
  id: string;
  lead_id: string;
  company_name: string;
  status: string;
  progress: number;
  intent_score: number;
  intent_level: string;
  error_message?: string;
}

export interface SalesIntelligenceReport {
  id: string;
  lead_id: string;
  company_name: string;
  website_url?: string;
  status: string;
  progress: number;
  intent_score: number;
  intent_level: string;
  intent_reason?: string;
  decision_makers: DecisionMaker[];
  growth_signals: GrowthSignal[];
  timeline?: CompanyTimeline;
  classification?: SalesOpportunityClassification;
  graph?: RelationshipGraph;
  recommendations?: SalesRecommendation;
  analyzed_at?: string;
  created_at: string;
  updated_at: string;
}

export const salesIntelligenceApi = {
  analyzeLead: async (leadId: string): Promise<SalesIntelligenceStatusResponse> => {
    const res = await axiosClient.post<SalesIntelligenceStatusResponse>('/sales-intelligence/analyze', {
      lead_id: leadId,
    });
    return res.data;
  },

  getReportByLead: async (leadId: string): Promise<SalesIntelligenceReport | null> => {
    try {
      const res = await axiosClient.get<SalesIntelligenceReport>(`/sales-intelligence/lead/${leadId}`);
      return res.data;
    } catch (err: any) {
      if (err.response?.status === 404) {
        return null;
      }
      throw err;
    }
  },

  getJobStatus: async (jobId: string): Promise<SalesIntelligenceStatusResponse> => {
    const res = await axiosClient.get<SalesIntelligenceStatusResponse>(`/sales-intelligence/${jobId}/status`);
    return res.data;
  },

  getGrowthSignals: async (leadId: string): Promise<GrowthSignal[]> => {
    const res = await axiosClient.get<GrowthSignal[]>(`/sales-intelligence/${leadId}/signals`);
    return res.data;
  },

  getDecisionMakers: async (leadId: string): Promise<DecisionMaker[]> => {
    const res = await axiosClient.get<DecisionMaker[]>(`/sales-intelligence/${leadId}/decision-makers`);
    return res.data;
  },

  getTimeline: async (leadId: string): Promise<CompanyTimeline> => {
    const res = await axiosClient.get<CompanyTimeline>(`/sales-intelligence/${leadId}/timeline`);
    return res.data;
  },

  getRecommendations: async (leadId: string): Promise<SalesRecommendation> => {
    const res = await axiosClient.get<SalesRecommendation>(`/sales-intelligence/${leadId}/recommendations`);
    return res.data;
  },

  deleteReport: async (leadId: string): Promise<{ status: string; message: string }> => {
    const res = await axiosClient.delete<{ status: string; message: string }>(`/sales-intelligence/lead/${leadId}`);
    return res.data;
  },
};
