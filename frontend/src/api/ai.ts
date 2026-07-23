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
  system_prompt_template?: string;
  user_prompt_template: string;
  variables: string[];
  created_by: string;
  created_at: string;
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
    user_prompt_template: string;
    system_prompt_template?: string;
    variables: string[];
    changes_description?: string;
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
};
export default aiApi;
