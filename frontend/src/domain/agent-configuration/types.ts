import type { PageResult } from "@/shared/types/list";

export type AgentStatus = "draft" | "active" | "disabled" | "archived";
export type AgentOrchestrationMode = "agent" | "chatbot" | "workflow";

export interface AgentListQuery {
  keyword?: string;
  status?: AgentStatus;
  orchestrationMode?: AgentOrchestrationMode;
  providerModelId?: number;
}

export interface AgentModelSummary {
  providerInstanceId: number;
  providerName: string | null;
  providerType: string | null;
  modelId: number;
  modelName: string;
  displayName: string;
}

export interface AgentToolBinding {
  toolId: number;
  bindingName: string | null;
  isEnabled: boolean;
  sortOrder: number;
  config: Record<string, unknown> | null;
  metadata?: Record<string, unknown> | null;
}

export interface AgentKnowledgeBinding {
  knowledgeBaseId: number;
  isEnabled: boolean;
  sortOrder: number;
  retrievalConfig: Record<string, unknown> | null;
  metadata?: Record<string, unknown> | null;
}

export interface AgentSummaryRecord {
  id: number;
  name: string;
  description: string | null;
  avatarUrl: string | null;
  status: AgentStatus;
  orchestrationMode: AgentOrchestrationMode;
  providerInstanceId: number | null;
  providerModelId: number | null;
  model: AgentModelSummary | null;
  toolCount: number;
  knowledgeBaseCount: number;
  tags: string[];
  createdAt: string;
  updatedAt: string;
}

export interface AgentDetailRecord extends AgentSummaryRecord {
  systemPrompt: string | null;
  openingMessage: string | null;
  modelConfig: Record<string, unknown> | null;
  runtimeConfig: Record<string, unknown> | null;
  workflowRef: Record<string, unknown> | null;
  tools: AgentToolBinding[];
  knowledgeBases: AgentKnowledgeBinding[];
  metadata: Record<string, unknown> | null;
}

export interface AgentConfigPreviewRecord {
  agentId: number;
  name: string;
  status: AgentStatus;
  orchestrationMode: AgentOrchestrationMode;
  isRunnable: boolean;
  model: AgentModelSummary | null;
  enabledToolIds: number[];
  enabledKnowledgeBaseIds: number[];
  runtimeConfig: Record<string, unknown> | null;
  workflowRef: Record<string, unknown> | null;
  warnings: string[];
}

export type AgentListResult = PageResult<AgentSummaryRecord>;

export interface AgentFormValues {
  name: string;
  description?: string;
  avatarUrl?: string;
  status: AgentStatus;
  orchestrationMode: AgentOrchestrationMode;
  providerInstanceId?: number;
  providerModelId?: number;
  systemPrompt?: string;
  openingMessage?: string;
  modelConfig?: Record<string, unknown> | null;
  runtimeConfig?: Record<string, unknown> | null;
  workflowRef?: Record<string, unknown> | null;
  tools: AgentToolBinding[];
  knowledgeBases: AgentKnowledgeBinding[];
  tags: string[];
}
