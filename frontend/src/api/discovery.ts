import axiosClient from './axiosClient';

export interface DiscoveryStartPayload {
  keyword: string;
  location: string;
  providers: string[];
  website_filter?: string;
  limit?: number;
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

export interface DiscoveredCompany {
  id: string;
  name?: string;
  company_name?: string;
  trade_name?: string;
  fingerprint?: string;
  is_merged?: boolean;
  merged_from?: string[];
  phone?: string;
  phones?: string[];
  email?: string;
  emails?: string[];
  website?: string;
  website_domain?: string;
  address?: string;
  city?: string;
  location?: string;
  state?: string;
  postal_code?: string;
  country?: string;
  coordinates?: { lat: number; lng: number };
  gst?: string;
  categories?: string[];
  industry?: string;
  products?: string[];
  business_type?: string;
  rating?: number;
  review_count?: number;
  photos?: string[];
  ai_summary?: string;
  business_maturity?: string;
  buyer_intent?: string;
  employees_estimate?: string;
  score?: number;
  quality_score?: number;
  quality_tier?: string;
  scoring_breakdown?: Record<string, number>;
  sources?: Array<{ provider: string; raw_name?: string; raw_phone?: string }>;
  provider?: string;
  source_providers?: string[];
  crm_created?: boolean;
  knowledge_created?: boolean;
}

export interface DuplicateMergeLog {
  canonical_fingerprint: string;
  merged_fingerprints: string[];
  merged_company_names: string[];
  merged_providers: string[];
  match_reasons: string[];
  confidence: number;
}

export interface ProviderHealth {
  provider: string;
  status: string;
  circuit_state: string;
  requests_per_minute_quota: number;
  total_requests: number;
  success_count: number;
  failure_count: number;
  avg_latency_ms: number;
  last_error?: string;
  capabilities: Record<string, any>;
}

export interface DiscoveryAnalytics {
  summary: {
    businesses_discovered_total: number;
    duplicates_merged_total: number;
    deduplication_rate_percent: number;
    avg_enrichment_time_ms: number;
    avg_quality_score: number;
  };
  quality_distribution: {
    hot: number;
    warm: number;
    cold: number;
  };
  provider_health: {
    total_providers: number;
    healthy_count: number;
    degraded_count: number;
    down_count: number;
    providers: Record<string, ProviderHealth>;
  };
}

export const startDiscoveryJob = async (payload: DiscoveryStartPayload): Promise<JobStatusResponse> => {
  const response = await axiosClient.post('/discovery/start', payload);
  return response.data;
};

export const getLatestJob = async (): Promise<JobStatusResponse> => {
  const response = await axiosClient.get('/discovery/jobs/latest');
  return response.data;
};

export const getAllDiscoveredCompanies = async (): Promise<DiscoveredCompany[]> => {
  const response = await axiosClient.get('/discovery/all/companies');
  return response.data;
};

export const getJobStatus = async (jobId: string): Promise<JobStatusResponse> => {
  const response = await axiosClient.get(`/discovery/${jobId}`);
  return response.data;
};

export const getJobResults = async (jobId: string): Promise<DiscoveredCompany[]> => {
  const response = await axiosClient.get(`/discovery/results/${jobId}`);
  return response.data;
};

export const getJobDuplicates = async (jobId: string): Promise<DuplicateMergeLog[]> => {
  const response = await axiosClient.get(`/discovery/duplicates/${jobId}`);
  return response.data;
};

export const getProviderHealth = async (): Promise<Record<string, any>> => {
  const response = await axiosClient.get('/discovery/providers');
  return response.data;
};

export const getDiscoveryAnalytics = async (): Promise<DiscoveryAnalytics> => {
  const response = await axiosClient.get('/discovery/analytics/dashboard');
  return response.data;
};

export const saveLeadsToCRM = async (jobId: string, leadIds: string[]): Promise<any> => {
  const response = await axiosClient.post(`/discovery/results/${jobId}/save`, { lead_ids: leadIds });
  return response.data;
};
