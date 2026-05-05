import { agentConfigurationApi } from "@/domain/agent-configuration/api";
import type {
  AgentConfigPreviewRecord,
  AgentDetailRecord,
  AgentFormValues,
  AgentListQuery,
  AgentListResult,
  AgentToolBinding,
  AgentKnowledgeBinding,
} from "@/domain/agent-configuration/types";
import { request } from "@/shared/api";
import type { QueryParams } from "@/shared/api/types";
import type { ListRequestParams } from "@/shared/types/list";

function normalizeOptionalText(value: string | undefined): string | null {
  const trimmedValue = value?.trim() ?? "";
  return trimmedValue === "" ? null : trimmedValue;
}

function normalizeNumber(value: number | undefined): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function normalizeToolBinding(
  binding: AgentToolBinding,
  index: number,
): AgentToolBinding {
  return {
    toolId: binding.toolId,
    bindingName: normalizeOptionalText(binding.bindingName ?? undefined),
    isEnabled: binding.isEnabled,
    sortOrder: binding.sortOrder ?? index,
    config: binding.config ?? null,
    metadata: binding.metadata ?? null,
  };
}

function normalizeKnowledgeBinding(
  binding: AgentKnowledgeBinding,
  index: number,
): AgentKnowledgeBinding {
  return {
    knowledgeBaseId: binding.knowledgeBaseId,
    isEnabled: binding.isEnabled,
    sortOrder: binding.sortOrder ?? index,
    retrievalConfig: binding.retrievalConfig ?? null,
    metadata: binding.metadata ?? null,
  };
}

function buildAgentPayload(values: AgentFormValues) {
  return {
    name: values.name,
    description: normalizeOptionalText(values.description),
    avatarUrl: normalizeOptionalText(values.avatarUrl),
    status: values.status,
    orchestrationMode: values.orchestrationMode,
    providerInstanceId: normalizeNumber(values.providerInstanceId),
    providerModelId: normalizeNumber(values.providerModelId),
    systemPrompt: normalizeOptionalText(values.systemPrompt),
    openingMessage: normalizeOptionalText(values.openingMessage),
    modelConfig: values.modelConfig ?? null,
    runtimeConfig: values.runtimeConfig ?? null,
    workflowRef: values.workflowRef ?? null,
    tools: values.tools.map(normalizeToolBinding),
    knowledgeBases: values.knowledgeBases.map(normalizeKnowledgeBinding),
    tags: values.tags,
    metadata: null,
  };
}

export async function fetchAgentList(
  params: ListRequestParams<AgentListQuery>,
  signal?: AbortSignal,
): Promise<AgentListResult> {
  return request<AgentListResult>({
    request: agentConfigurationApi.listAgents,
    query: params as unknown as QueryParams,
    signal,
  });
}

export async function fetchAgentDetail(
  agentId: string | number,
  signal?: AbortSignal,
): Promise<AgentDetailRecord> {
  return request<AgentDetailRecord>({
    request: agentConfigurationApi.getAgentDetail,
    pathParams: {
      agentId,
    },
    signal,
  });
}

export async function createAgent(
  values: AgentFormValues,
  signal?: AbortSignal,
): Promise<AgentDetailRecord> {
  return request<AgentDetailRecord>({
    request: agentConfigurationApi.createAgent,
    body: buildAgentPayload(values),
    signal,
  });
}

export async function updateAgent(
  agentId: string | number,
  values: AgentFormValues,
  signal?: AbortSignal,
): Promise<AgentDetailRecord> {
  return request<AgentDetailRecord>({
    request: agentConfigurationApi.updateAgent,
    pathParams: {
      agentId,
    },
    body: buildAgentPayload(values),
    signal,
  });
}

export async function deleteAgent(
  agentId: string | number,
  signal?: AbortSignal,
): Promise<void> {
  return request<void>({
    request: agentConfigurationApi.deleteAgent,
    pathParams: {
      agentId,
    },
    signal,
  });
}

export async function fetchAgentConfigPreview(
  agentId: string | number,
  signal?: AbortSignal,
): Promise<AgentConfigPreviewRecord> {
  return request<AgentConfigPreviewRecord>({
    request: agentConfigurationApi.getAgentConfigPreview,
    pathParams: {
      agentId,
    },
    signal,
  });
}
