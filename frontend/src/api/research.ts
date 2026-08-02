import axiosClient from "./axiosClient";

export interface VerifiedFact {
  fact: string;
  confidence: number;
  source: string;
  agent: string;
  timestamp: string;
  verification_method: string;
}

export interface WebsiteResearchFindings {
  executive_summary?: string;
  products: string[];
  services: string[];
  business_model?: string;
  target_customers: string[];
  markets: string[];
  technology: string[];
  pain_points: string[];
  crawled_pages: string[];
}

export interface NewsArticle {
  headline: string;
  summary: string;
  category: string;
  date?: string;
  source: string;
  confidence: number;
}

export interface NewsResearchFindings {
  articles: NewsArticle[];
}

export interface HiringDepartment {
  department: string;
  open_count: number;
  key_roles: string[];
}

export interface HiringResearchFindings {
  departments: HiringDepartment[];
  open_positions_count: number;
  hiring_velocity: string;
  growth_stage: string;
  expansion_signals: string[];
}

export interface TechnologyResearchFindings {
  frontend: string[];
  backend: string[];
  cloud_hosting: string[];
  analytics: string[];
  crm: string[];
  marketing: string[];
  payments: string[];
  cdn: string[];
  database: string[];
  security: string[];
  developer_tools: string[];
  languages_frameworks: string[];
  tech_maturity: string;
  migration_opportunities: string[];
}

export interface CompetitorItem {
  name: string;
  product_name?: string;
  market_position: string;
  pricing?: string;
  strengths: string[];
  weaknesses: string[];
  differentiators: string[];
}

export interface CompetitorResearchFindings {
  competitors: CompetitorItem[];
  market_position_summary?: string;
}

export interface SocialPlatform {
  platform: string;
  url?: string;
  posting_frequency: string;
  engagement_level: string;
  audience_growth_signal: string;
}

export interface SocialResearchFindings {
  platforms: SocialPlatform[];
  overall_presence_score: number;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
}

export interface GraphEdge {
  source_id: string;
  target_id: string;
  relation_type: string;
  weight: number;
}

export interface ResearchKnowledgeGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface SWOTAnalysis {
  strengths: string[];
  weaknesses: string[];
  opportunities: string[];
  threats: string[];
}

export interface AIResearchSummary {
  executive_summary?: string;
  swot?: SWOTAnalysis;
  business_overview?: string;
  sales_opportunity?: string;
  risks: string[];
  expansion_opportunities: string[];
  buying_signals: string[];
  pitch_angle?: string;
  objections: string[];
  recommended_strategy?: string;
}

export interface ResearchStatusResponse {
  id: string;
  lead_id: string;
  company_name: string;
  status: string;
  progress: number;
  overall_confidence: number;
  error_message?: string;
}

export interface ResearchReport {
  id: string;
  lead_id: string;
  company_name: string;
  website_url?: string;
  status: string;
  progress: number;
  overall_confidence: number;
  error_message?: string;

  website_findings?: WebsiteResearchFindings;
  news_findings?: NewsResearchFindings;
  hiring_findings?: HiringResearchFindings;
  tech_findings?: TechnologyResearchFindings;
  competitor_findings?: CompetitorResearchFindings;
  social_findings?: SocialResearchFindings;

  knowledge_graph?: ResearchKnowledgeGraph;
  verified_facts: VerifiedFact[];
  ai_summary?: AIResearchSummary;

  analyzed_at?: string;
  created_at: string;
  updated_at: string;
}

export const researchApi = {
  analyzeCompany: async (leadId: string) => {
    const response = await axiosClient.post<ResearchStatusResponse>("/research/analyze", {
      lead_id: leadId,
    });
    return response.data;
  },

  getJobStatus: async (jobId: string) => {
    const response = await axiosClient.get<ResearchStatusResponse>(`/research/${jobId}/status`);
    return response.data;
  },

  getReportByLead: async (leadId: string): Promise<ResearchReport | null> => {
    try {
      const response = await axiosClient.get<ResearchReport>(`/research/lead/${leadId}`);
      return response.data;
    } catch (err: any) {
      if (err.response?.status === 404) {
        return null;
      }
      throw err;
    }
  },

  getWebsiteResearch: async (leadId: string) => {
    const response = await axiosClient.get<WebsiteResearchFindings>(`/research/${leadId}/website`);
    return response.data;
  },

  getNewsResearch: async (leadId: string) => {
    const response = await axiosClient.get<NewsResearchFindings>(`/research/${leadId}/news`);
    return response.data;
  },

  getTechnologyResearch: async (leadId: string) => {
    const response = await axiosClient.get<TechnologyResearchFindings>(`/research/${leadId}/technology`);
    return response.data;
  },

  getHiringResearch: async (leadId: string) => {
    const response = await axiosClient.get<HiringResearchFindings>(`/research/${leadId}/hiring`);
    return response.data;
  },

  getCompetitorResearch: async (leadId: string) => {
    const response = await axiosClient.get<CompetitorResearchFindings>(`/research/${leadId}/competitors`);
    return response.data;
  },

  getSocialResearch: async (leadId: string) => {
    const response = await axiosClient.get<SocialResearchFindings>(`/research/${leadId}/social`);
    return response.data;
  },

  getKnowledgeGraph: async (leadId: string) => {
    const response = await axiosClient.get<ResearchKnowledgeGraph>(`/research/${leadId}/graph`);
    return response.data;
  },

  deleteReport: async (leadId: string) => {
    const response = await axiosClient.delete(`/research/lead/${leadId}`);
    return response.data;
  },
};
