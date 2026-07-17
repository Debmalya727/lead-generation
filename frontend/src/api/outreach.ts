import axiosClient from "./axiosClient";

export interface EmailAccount {
  id: string;
  owner_id: string;
  provider_type: string;
  name: string;
  email_address: string;
  smtp_host?: string;
  smtp_port?: number;
  smtp_username?: string;
  smtp_password?: string;
  daily_limit: number;
  sending_count_today: number;
  warmup_enabled: boolean;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface EmailTemplate {
  id: string;
  owner_id: string;
  name: string;
  category: string;
  subject: string;
  body: string;
  variables_used: string[];
  created_at: string;
  updated_at: string;
}

export interface CampaignStep {
  step_number: number;
  delay_days: number;
  step_type: string;
  subject: string;
  body: string;
  template_id?: string;
}

export interface Campaign {
  id: string;
  owner_id: string;
  name: string;
  status: string;
  sending_account_id?: string;
  daily_limit: number;
  ab_testing_enabled: boolean;
  schedule_config: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export interface CampaignDetail {
  campaign: Campaign;
  steps: CampaignStep[];
  recipients_count: number;
  analytics?: CampaignAnalytics;
}

export interface CampaignAnalytics {
  campaign_id: string;
  owner_id: string;
  total_recipients: number;
  total_sent: number;
  total_opened: number;
  total_clicked: number;
  total_replied: number;
  total_bounced: number;
  total_unsubscribed: number;
  open_rate: number;
  click_rate: number;
  reply_rate: number;
  bounce_rate: number;
}

export interface AIEmailGenerateRequest {
  lead_id: string;
  generation_type: "cold_email" | "followup" | "subject" | "icebreaker";
  value_proposition?: string;
  step_number?: number;
}

export interface AIResponse {
  subject?: string;
  icebreaker?: string;
  body?: string;
  cta?: string;
  subjects_list?: string[];
}

export const outreachApi = {
  // Accounts
  listAccounts: async (): Promise<EmailAccount[]> => {
    const res = await axiosClient.get("/outreach/accounts");
    return res.data;
  },
  createAccount: async (data: Partial<EmailAccount>): Promise<EmailAccount> => {
    const res = await axiosClient.post("/outreach/accounts", data);
    return res.data;
  },
  deleteAccount: async (accountId: string): Promise<void> => {
    await axiosClient.delete(`/outreach/accounts/${accountId}`);
  },
  testAccount: async (accountId: string, recipientEmail: string): Promise<{ status: string; message: string }> => {
    const res = await axiosClient.post(`/outreach/accounts/${accountId}/test?recipient_email=${encodeURIComponent(recipientEmail)}`);
    return res.data;
  },

  // Templates
  listTemplates: async (): Promise<EmailTemplate[]> => {
    const res = await axiosClient.get("/outreach/templates");
    return res.data;
  },
  createTemplate: async (data: Partial<EmailTemplate>): Promise<EmailTemplate> => {
    const res = await axiosClient.post("/outreach/templates", data);
    return res.data;
  },
  updateTemplate: async (templateId: string, data: Partial<EmailTemplate>): Promise<EmailTemplate> => {
    const res = await axiosClient.put(`/outreach/templates/${templateId}`, data);
    return res.data;
  },
  deleteTemplate: async (templateId: string): Promise<void> => {
    await axiosClient.delete(`/outreach/templates/${templateId}`);
  },

  // Campaigns
  listCampaigns: async (): Promise<Campaign[]> => {
    const res = await axiosClient.get("/outreach/campaigns");
    return res.data;
  },
  getCampaignDetail: async (campaignId: string): Promise<CampaignDetail> => {
    const res = await axiosClient.get(`/outreach/campaigns/${campaignId}`);
    return res.data;
  },
  createCampaign: async (payload: {
    name: string;
    sending_account_id?: string;
    daily_limit?: number;
    ab_testing_enabled?: boolean;
    steps: CampaignStep[];
    lead_ids: string[];
  }): Promise<Campaign> => {
    const res = await axiosClient.post("/outreach/campaigns", payload);
    return res.data;
  },
  updateCampaignStatus: async (campaignId: string, status: string): Promise<Campaign> => {
    const res = await axiosClient.put(`/outreach/campaigns/${campaignId}/status`, { status });
    return res.data;
  },
  deleteCampaign: async (campaignId: string): Promise<void> => {
    await axiosClient.delete(`/outreach/campaigns/${campaignId}`);
  },

  // AI Generation & Preview
  generateAiCopy: async (req: AIEmailGenerateRequest): Promise<AIResponse> => {
    const res = await axiosClient.post("/outreach/ai/generate", req);
    return res.data;
  },
  previewEmail: async (req: { lead_id: string; subject_template: string; body_template: string }): Promise<{ rendered_subject: string; rendered_body: string }> => {
    const res = await axiosClient.post("/outreach/preview", req);
    return res.data;
  },

  // Analytics
  getAnalytics: async (campaignId: string): Promise<CampaignAnalytics> => {
    const res = await axiosClient.get(`/outreach/analytics/${campaignId}`);
    return res.data;
  },
};
