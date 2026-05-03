import type { PageResult } from "@/shared/types/list";

export interface ProviderListQuery {
  keyword?: string;
  providerType?: string;
  status?: string;
}

export interface ProviderAuthSummary {
  authType: string;
  secretMasked: string;
  hasSecret: boolean;
  expiresAt: string | null;
  lastRotatedAt: string | null;
}

export interface ProviderModelRecord {
  id: number;
  modelName: string;
  displayName: string;
  description: string | null;
  status: string;
  isDefault: boolean;
  sortOrder: number;
  supportsChat: boolean;
  supportsStream: boolean;
  supportsTools: boolean;
  supportsStructuredOutput: boolean;
  supportsVisionInput: boolean;
  supportsAudioInput: boolean;
  supportsReasoning: boolean;
  supportsEmbeddings: boolean;
  contextWindow: number | null;
  maxOutputTokens: number | null;
  maxInputTokens: number | null;
  temperatureSupported: boolean;
  topPSupported: boolean;
  tags: string[] | null;
  pricing: Record<string, unknown> | null;
  metadata: Record<string, unknown> | null;
  createdAt: string;
  updatedAt: string;
}

export interface ProviderHealthSummary {
  healthState: string;
  authState: string;
  connectivityState: string;
  inferenceState: string;
  lastCheckAt: string | null;
  lastSuccessAt: string | null;
  lastFailureAt: string | null;
  consecutiveFailures: number;
  latencyMsP50: number | null;
  latencyMsP95: number | null;
  lastErrorCode: string | null;
  lastErrorMessage: string | null;
  lastErrorAt: string | null;
}

export interface ProviderConnectionTestResult {
  providerId: number;
  healthState: string;
  authState: string;
  connectivityState: string;
  inferenceState: string;
  httpStatusCode: number;
  latencyMs: number | null;
  message: string;
  checkedAt: string;
}

export interface ProviderRuntimeConfigRecord {
  providerId: number;
  providerType: string;
  apiFamily: string;
  modelName: string;
  litellmModel: string;
  apiBase: string;
  apiKeyMasked: string;
  extraHeaders: Record<string, string>;
  queryParams: Record<string, string>;
}

export interface ProviderInvokeTestPayload {
  prompt: string;
  modelName?: string;
  temperature?: number;
  maxTokens?: number;
}

export interface ProviderInvokeTestResult {
  providerId: number;
  modelName: string;
  litellmModel: string;
  outputText: string;
  latencyMs: number;
}

export interface ProviderSummaryRecord {
  id: number;
  name: string;
  providerType: string;
  apiFamily: string;
  baseUrl: string;
  status: string;
  isDefault: boolean;
  priority: number;
  notes: string | null;
  metadata: Record<string, unknown> | null;
  modelCount: number;
  auth: ProviderAuthSummary | null;
  defaultModel: ProviderModelRecord | null;
  health: ProviderHealthSummary | null;
  createdAt: string;
  updatedAt: string;
}

export interface ProviderDetailRecord extends ProviderSummaryRecord {
  models: ProviderModelRecord[];
}

export type ProviderListResult = PageResult<ProviderSummaryRecord>;

export interface ProviderModelFormValue {
  modelName: string;
  displayName: string;
  description?: string;
  status: string;
  isDefault: boolean;
  sortOrder: number;
  supportsChat: boolean;
  supportsStream: boolean;
  supportsTools: boolean;
  supportsStructuredOutput: boolean;
  supportsVisionInput: boolean;
  supportsAudioInput: boolean;
  supportsReasoning: boolean;
  supportsEmbeddings: boolean;
  contextWindow?: number;
  maxOutputTokens?: number;
  maxInputTokens?: number;
  temperatureSupported: boolean;
  topPSupported: boolean;
}

export interface ProviderFormValues {
  name: string;
  providerType: string;
  apiFamily: string;
  baseUrl: string;
  status: string;
  isDefault: boolean;
  priority: number;
  notes?: string;
  authType: string;
  secretValue?: string;
  models: ProviderModelFormValue[];
}
