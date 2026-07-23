import axiosClient from "./axiosClient";

export interface VectorStatusResponse {
  provider: string;
  status: string;
  total_chunks: number;
  collections: Record<string, number>;
}

export interface VectorSearchResultItem {
  chunk_id: string;
  document_id: string;
  lead_id?: string;
  collection_name: string;
  title: string;
  content: string;
  score: number;
  metadata: Record<string, any>;
  created_at: string;
}

export interface VectorSearchResponse {
  query: string;
  total_matches: number;
  results: VectorSearchResultItem[];
}

export interface RAGSourceCitation {
  doc_num: number;
  collection: string;
  document_id: string;
  lead_id?: string;
  title: string;
  score: number;
  content_snippet: string;
  metadata: Record<string, any>;
}

export interface RAGQueryResponse {
  question: string;
  answer: string;
  confidence_score: number;
  summary_points: string[];
  sources: RAGSourceCitation[];
}

export const knowledgeApi = {
  getVectorStatus: async () => {
    const response = await axiosClient.get<VectorStatusResponse>("/vector/status");
    return response.data;
  },

  indexLeadKnowledge: async (leadId: string) => {
    const response = await axiosClient.post("/vector/index", { lead_id: leadId });
    return response.data;
  },

  reindexWorkspace: async () => {
    const response = await axiosClient.post("/vector/reindex");
    return response.data;
  },

  searchVectors: async (params: {
    query: string;
    collection_name?: string;
    lead_id?: string;
    top_k?: number;
    score_threshold?: number;
  }) => {
    const response = await axiosClient.post<VectorSearchResponse>("/vector/search", params);
    return response.data;
  },

  queryRAGPipeline: async (params: {
    question: string;
    collection_name?: string;
    lead_id?: string;
    top_k?: number;
  }) => {
    const response = await axiosClient.post<RAGQueryResponse>("/rag/query", params);
    return response.data;
  },

  deleteDocumentChunks: async (documentId: string) => {
    const response = await axiosClient.delete(`/vector/document/${documentId}`);
    return response.data;
  },
};
