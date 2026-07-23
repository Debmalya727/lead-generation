import axiosClient from "./axiosClient";

export interface ActionCard {
  title: string;
  description: string;
  action_type: string;
  payload: Record<string, any>;
  button_label: string;
}

export interface ChatMessage {
  message_id: string;
  session_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  intent?: string;
  confidence?: number;
  entities?: Record<string, any>;
  execution_id?: string;
  action_cards: ActionCard[];
  execution_visualization?: Record<string, any>;
  timestamp: string;
}

export interface ChatSession {
  session_id: string;
  title: string;
  is_pinned: boolean;
  is_archived: boolean;
  active_company_name?: string;
  last_intent?: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export const chatApi = {
  sendMessage: async (payload: { message: string; session_id?: string; company_name?: string }) => {
    const res = await axiosClient.post<ChatMessage>("/chat", payload);
    return res.data;
  },

  listSessions: async (params?: { limit?: number; skip?: number }) => {
    const res = await axiosClient.get<{ total_count: number; items: ChatSession[] }>("/chat/sessions", { params });
    return res.data;
  },

  getSession: async (sessionId: string) => {
    const res = await axiosClient.get<ChatSession>(`/chat/session/${sessionId}`);
    return res.data;
  },

  getHistory: async (sessionId: string, limit: number = 50) => {
    const res = await axiosClient.get<ChatMessage[]>("/chat/history", { params: { session_id: sessionId, limit } });
    return res.data;
  },

  deleteSession: async (sessionId: string) => {
    const res = await axiosClient.delete<{ status: string; session_id: string }>(`/chat/session/${sessionId}`);
    return res.data;
  },

  submitFeedback: async (payload: { session_id: string; message_id: string; rating: number; comments?: string; category?: string }) => {
    const res = await axiosClient.post("/chat/feedback", payload);
    return res.data;
  },
};
