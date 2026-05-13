import type { PageResult } from "@/shared/types/list";

export type KnowledgeBaseStatus = "draft" | "enabled" | "archived";
export type KnowledgeVisibility = "private" | "workspace";
export type KnowledgeDocumentStatus =
  | "uploaded"
  | "processing"
  | "completed"
  | "failed"
  | "disabled";

export interface KnowledgeBaseListQuery {
  keyword?: string;
  status?: KnowledgeBaseStatus;
  visibility?: KnowledgeVisibility;
}

export interface KnowledgeBaseSummary {
  id: number;
  name: string;
  description: string | null;
  status: KnowledgeBaseStatus;
  visibility: KnowledgeVisibility;
  documentCount: number;
  chunkCount: number;
  lastIndexedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface KnowledgeHealth {
  score: number;
  label: string;
  suggestion: string | null;
}

export interface KnowledgeBoundAgent {
  agentId: number;
  agentName: string;
  isEnabled: boolean;
  topK: number | null;
  scoreThreshold: number | null;
}

export interface KnowledgeBaseOption {
  id: number;
  name: string;
  status: KnowledgeBaseStatus;
  documentCount: number;
  chunkCount: number;
}

export interface KnowledgeBaseDetail extends KnowledgeBaseSummary {
  embeddingModel: string;
  embeddingDimensions: number;
  chunkSize: number;
  chunkOverlap: number;
  defaultTopK: number;
  defaultScoreThreshold: number;
  processingDocumentCount: number;
  failedDocumentCount: number;
  health: KnowledgeHealth;
  boundAgents: KnowledgeBoundAgent[];
  metadata: Record<string, unknown> | null;
}

export interface KnowledgeBaseFormValues {
  name: string;
  description?: string;
  status: KnowledgeBaseStatus;
  visibility: KnowledgeVisibility;
  chunkSize: number;
  chunkOverlap: number;
  defaultTopK: number;
  defaultScoreThreshold: number;
}

export interface KnowledgeDocumentQuery {
  keyword?: string;
  status?: KnowledgeDocumentStatus;
}

export interface KnowledgeDocumentRecord {
  id: number;
  knowledgeBaseId: number;
  filename: string;
  fileExt: string;
  mimeType: string | null;
  fileSizeBytes: number;
  status: KnowledgeDocumentStatus;
  processStage: string;
  chunkCount: number;
  tokenCount: number;
  errorCode: string | null;
  errorMessage: string | null;
  startedAt: string | null;
  completedAt: string | null;
  createdAt: string;
  updatedAt: string;
  metadata: Record<string, unknown> | null;
}

export interface RetrievalTestPayload {
  query: string;
  topK?: number;
  scoreThreshold?: number;
}

export interface RetrievalHit {
  chunkId: number;
  documentId: number;
  documentName: string;
  content: string;
  score: number;
  pageNumber: number | null;
  sectionTitle: string | null;
}

export interface RetrievalTestResult {
  query: string;
  topK: number;
  scoreThreshold: number;
  latencyMs: number;
  hits: RetrievalHit[];
}

export type KnowledgeBaseListResult = PageResult<KnowledgeBaseSummary>;
export type KnowledgeDocumentListResult = PageResult<KnowledgeDocumentRecord>;
