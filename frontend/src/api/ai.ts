import axiosClient from "./axiosClient";

export interface AIProviderItem {
  provider: string;
  status: string;
}

export interface AIModelItem {
  model_id: string;
  provider: string;
  name: string;
  capabilities: string[];
  context_window: number;
  input_token_price: number;
  output_token_price: number;
  is_embedding: boolean;
}

export interface AIPromptTemplateItem {
  template_id: string;
  name: string;
  category: string;
  tags?: string[];
  system_prompt_template?: string;
  user_prompt_template: string;
  variables: string[];
  current_version?: number;
  version_tag?: string;
  status?: string;
  hit_count?: number;
  created_by?: string;
  created_at?: string;
}

export interface AICostItem {
  identifier_type: string;
  identifier_id: string;
  estimated_cost: number;
  currency: string;
  updated_at: string;
}

export interface AITokenItem {
  identifier_type: string;
  identifier_id: string;
  prompt_tokens: number;
  completion_tokens: number;
  embedding_tokens: number;
  total_tokens: number;
  updated_at: string;
}

export const aiApi = {
  getProviders: async () => {
    const res = await axiosClient.get<AIProviderItem[]>("/ai/providers");
    return res.data;
  },

  getModels: async () => {
    const res = await axiosClient.get<AIModelItem[]>("/ai/models");
    return res.data;
  },

  getPrompts: async () => {
    const res = await axiosClient.get<AIPromptTemplateItem[]>("/ai/prompts");
    return res.data;
  },

  savePrompt: async (payload: {
    template_id: string;
    name: string;
    category: string;
    tags?: string[];
    user_prompt_template: string;
    system_prompt_template?: string;
    variables?: string[];
    changes_description?: string;
    author?: string;
  }) => {
    const res = await axiosClient.post<AIPromptTemplateItem>("/ai/prompts", payload);
    return res.data;
  },

  getCosts: async (identifierType?: string) => {
    const res = await axiosClient.get<AICostItem[]>("/ai/costs", {
      params: { identifier_type: identifierType },
    });
    return res.data;
  },

  getTokens: async (identifierType?: string) => {
    const res = await axiosClient.get<AITokenItem[]>("/ai/tokens", {
      params: { identifier_type: identifierType },
    });
    return res.data;
  },

  testChat: async (payload: {
    prompt: string;
    system_prompt?: string;
    provider: string;
    model: string;
  }) => {
    const res = await axiosClient.post("/ai/chat", { ...payload, stream: false });
    return res.data;
  },

  getCacheStats: async () => {
    const res = await axiosClient.get("/ai/cache/stats");
    return res.data;
  },

  clearCache: async (scope: string = "all") => {
    const res = await axiosClient.post("/ai/cache/clear", { scope });
    return res.data;
  },

  warmCache: async (items: Array<Record<string, any>>) => {
    const res = await axiosClient.post("/ai/cache/warm", { items });
    return res.data;
  },

  exportCache: async () => {
    const res = await axiosClient.get("/ai/cache/export");
    return res.data;
  },

  getPromptHistory: async (templateId: string) => {
    const res = await axiosClient.get(`/ai/prompts/${templateId}/history`);
    return res.data;
  },

  getPromptDiff: async (templateId: string, versionA: number, versionB: number) => {
    const res = await axiosClient.get(`/ai/prompts/${templateId}/diff`, {
      params: { version_a: versionA, version_b: versionB },
    });
    return res.data;
  },

  rollbackPrompt: async (templateId: string, targetVersion: number) => {
    const res = await axiosClient.post(`/ai/prompts/${templateId}/rollback`, {
      target_version: targetVersion,
    });
    return res.data;
  },

  updatePromptApproval: async (templateId: string, status: string) => {
    const res = await axiosClient.post(`/ai/prompts/${templateId}/approval`, { status });
    return res.data;
  },

  publishPrompt: async (templateId: string, version?: number) => {
    const res = await axiosClient.post(`/ai/prompts/${templateId}/publish`, { version });
    return res.data;
  },

  testPromptTemplate: async (templateId: string, payload: { variables: Record<string, any>; provider: string; model: string }) => {
    const res = await axiosClient.post(`/ai/prompts/${templateId}/test`, payload);
    return res.data;
  },

  createPromptABTest: async (payload: {
    test_id: string;
    template_id: string;
    name: string;
    variant_a_version: number;
    variant_b_version: number;
    traffic_split_percent?: number;
  }) => {
    const res = await axiosClient.post("/ai/prompts/ab-tests", payload);
    return res.data;
  },

  getPromptABTest: async (testId: string) => {
    const res = await axiosClient.get(`/ai/prompts/ab-tests/${testId}`);
    return res.data;
  },

  getTools: async (category?: string) => {
    const res = await axiosClient.get("/ai/tools", { params: { category } });
    return res.data;
  },

  getOpenAIToolSchemas: async (category?: string) => {
    const res = await axiosClient.get("/ai/tools/schemas/openai", { params: { category } });
    return res.data;
  },

  getGeminiToolSchemas: async (category?: string) => {
    const res = await axiosClient.get("/ai/tools/schemas/gemini", { params: { category } });
    return res.data;
  },

  getToolMetrics: async () => {
    const res = await axiosClient.get("/ai/tools/metrics");
    return res.data;
  },

  getToolLogs: async (limit: number = 50) => {
    const res = await axiosClient.get("/ai/tools/logs", { params: { limit } });
    return res.data;
  },

  executeTool: async (payload: { tool_name: string; arguments: Record<string, any>; user_scopes?: string[] }) => {
    const res = await axiosClient.post("/ai/tools/execute", payload);
    return res.data;
  },

  getAgents: async () => {
    const res = await axiosClient.get("/ai/agents");
    return res.data;
  },

  getMarketplaceAgents: async () => {
    const res = await axiosClient.get("/ai/agents/marketplace");
    return res.data;
  },

  installMarketplaceAgent: async (templateId: string) => {
    const res = await axiosClient.post("/ai/agents/marketplace/install", { template_id: templateId });
    return res.data;
  },

  getAgentMetrics: async () => {
    const res = await axiosClient.get("/ai/agents/metrics");
    return res.data;
  },

  runAgent: async (agentId: string, goal: string, userScopes?: string[]) => {
    const res = await axiosClient.post(`/ai/agents/${agentId}/run`, { goal, user_scopes: userScopes });
    return res.data;
  },

  runAgentTeam: async (payload: {
    team_name: string;
    participating_agent_ids: string[];
    goal: string;
    user_scopes?: string[];
  }) => {
    const res = await axiosClient.post("/ai/agents/teams/run", payload);
    return res.data;
  },

  getObservabilityOverview: async () => {
    const res = await axiosClient.get("/ai/observability/overview");
    return res.data;
  },

  getDistributedTraces: async (limit: number = 50) => {
    const res = await axiosClient.get("/ai/observability/traces", { params: { limit } });
    return res.data;
  },

  getObservabilityAlerts: async (limit: number = 50) => {
    const res = await axiosClient.get("/ai/observability/alerts", { params: { limit } });
    return res.data;
  },

  triggerObservabilityAlert: async (payload: {
    alert_type: string;
    severity: string;
    source_component: string;
    message: string;
  }) => {
    const res = await axiosClient.post("/ai/observability/alerts/trigger", payload);
    return res.data;
  },

  getPrometheusMetrics: async () => {
    const res = await axiosClient.get("/ai/metrics", { responseType: "text" });
    return res.data;
  },

  getSecurityOverview: async () => {
    const res = await axiosClient.get("/ai/security/overview");
    return res.data;
  },

  getSecurityAuditLogs: async (limit: number = 50) => {
    const res = await axiosClient.get("/ai/security/audit-logs", { params: { limit } });
    return res.data;
  },

  encryptSecret: async (plaintext: string) => {
    const res = await axiosClient.post("/ai/security/encrypt", { plaintext });
    return res.data;
  },

  decryptSecret: async (ciphertext: string) => {
    const res = await axiosClient.post("/ai/security/decrypt", { ciphertext });
    return res.data;
  },

  rotateMasterKeys: async () => {
    const res = await axiosClient.post("/ai/security/rotate-keys");
    return res.data;
  },

  scanPromptInjection: async (prompt: string) => {
    const res = await axiosClient.post("/ai/security/scan-prompt", { prompt });
    return res.data;
  },

  scanFileMalware: async (payload: { filename: string; file_b64: string }) => {
    const res = await axiosClient.post("/ai/security/scan-file", payload);
    return res.data;
  },

  sendEmail: async (payload: {
    to_email: string;
    subject: string;
    html_content: string;
    variables?: Record<string, any>;
  }) => {
    const res = await axiosClient.post("/ai/email/send", payload);
    return res.data;
  },

  compileEmailTemplate: async (payload: {
    template_str: string;
    variables?: Record<string, any>;
    is_mjml?: boolean;
  }) => {
    const res = await axiosClient.post("/ai/email/compile-template", payload);
    return res.data;
  },

  launchEmailCampaign: async (payload: {
    name: string;
    subject: string;
    template_html: string;
    recipients: any[];
  }) => {
    const res = await axiosClient.post("/ai/email/campaigns", payload);
    return res.data;
  },

  getEmailAnalytics: async () => {
    const res = await axiosClient.get("/ai/email/analytics");
    return res.data;
  },

  getEmailWebhookEvents: async (limit: number = 50) => {
    const res = await axiosClient.get("/ai/email/webhooks/events", { params: { limit } });
    return res.data;
  },

  executePlaygroundSingle: async (payload: {
    prompt: string;
    provider?: string;
    model?: string;
    system_prompt?: string;
    temperature?: number;
    top_p?: number;
    max_tokens?: number;
    json_mode?: boolean;
  }) => {
    const res = await axiosClient.post("/ai/playground/execute", payload);
    return res.data;
  },

  executePlaygroundCompare: async (payload: {
    prompt: string;
    targets: Array<{ provider: string; model?: string }>;
    system_prompt?: string;
    temperature?: number;
    top_p?: number;
    max_tokens?: number;
    json_mode?: boolean;
  }) => {
    const res = await axiosClient.post("/ai/playground/compare", payload);
    return res.data;
  },

  savePlaygroundSession: async (payload: {
    title: string;
    prompt: string;
    runs: any[];
    system_prompt?: string;
    hyperparameters?: any;
  }) => {
    const res = await axiosClient.post("/ai/playground/sessions", payload);
    return res.data;
  },

  getPlaygroundSessions: async (limit: number = 50) => {
    const res = await axiosClient.get("/ai/playground/sessions", { params: { limit } });
    return res.data;
  },

  exportPlaygroundResults: async (payload: { session_data: any; format_type: string }) => {
    const res = await axiosClient.post("/ai/playground/export", payload, { responseType: "text" });
    return res.data;
  },
};
export default aiApi;
