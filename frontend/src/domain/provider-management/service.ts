import { request } from "@/shared/api";
import type { QueryParams } from "@/shared/api/types";
import type { ListRequestParams } from "@/shared/types/list";
import { providerManagementApi } from "@/domain/provider-management/api";
import type {
  ProviderConnectionTestResult,
  ProviderDetailRecord,
  ProviderFormValues,
  ProviderInvokeTestPayload,
  ProviderInvokeTestResult,
  ProviderListQuery,
  ProviderListResult,
  ProviderModelFormValue,
  ProviderRuntimeConfigRecord,
} from "@/domain/provider-management/types";

function normalizeModelPayload(model: ProviderModelFormValue, index: number) {
  return {
    modelName: model.modelName,
    displayName: model.displayName,
    description: model.description?.trim() || null,
    status: model.status,
    isDefault: model.isDefault,
    sortOrder: model.sortOrder ?? index,
    supportsChat: model.supportsChat,
    supportsStream: model.supportsStream,
    supportsTools: model.supportsTools,
    supportsStructuredOutput: model.supportsStructuredOutput,
    supportsVisionInput: model.supportsVisionInput,
    supportsAudioInput: model.supportsAudioInput,
    supportsReasoning: model.supportsReasoning,
    supportsEmbeddings: model.supportsEmbeddings,
    contextWindow: model.contextWindow ?? null,
    maxOutputTokens: model.maxOutputTokens ?? null,
    maxInputTokens: model.maxInputTokens ?? null,
    temperatureSupported: model.temperatureSupported,
    topPSupported: model.topPSupported,
    tags: null,
    pricing: null,
    metadata: null,
  };
}

function buildProviderPayload(values: ProviderFormValues) {
  return {
    name: values.name,
    providerType: values.providerType,
    apiFamily: values.apiFamily,
    baseUrl: values.baseUrl,
    status: values.status,
    isDefault: values.isDefault,
    priority: values.priority,
    notes: values.notes?.trim() || null,
    metadata: null,
    auth: {
      authType: values.authType,
      secretValue: values.secretValue?.trim() || null,
      headers: null,
      queryParams: null,
      metadata: null,
      expiresAt: null,
    },
    models: values.models.map(normalizeModelPayload),
  };
}

export async function fetchProviderList(
  params: ListRequestParams<ProviderListQuery>,
  signal?: AbortSignal,
): Promise<ProviderListResult> {
  return request<ProviderListResult>({
    request: providerManagementApi.listProviders,
    query: params as unknown as QueryParams,
    signal,
  });
}

export async function fetchProviderDetail(
  providerId: string | number,
  signal?: AbortSignal,
): Promise<ProviderDetailRecord> {
  return request<ProviderDetailRecord>({
    request: providerManagementApi.getProviderDetail,
    pathParams: {
      providerId,
    },
    signal,
  });
}

export async function createProvider(
  values: ProviderFormValues,
  signal?: AbortSignal,
): Promise<ProviderDetailRecord> {
  return request<ProviderDetailRecord>({
    request: providerManagementApi.createProvider,
    body: buildProviderPayload(values),
    signal,
  });
}

export async function updateProvider(
  providerId: string | number,
  values: ProviderFormValues,
  signal?: AbortSignal,
): Promise<ProviderDetailRecord> {
  return request<ProviderDetailRecord>({
    request: providerManagementApi.updateProvider,
    pathParams: {
      providerId,
    },
    body: buildProviderPayload(values),
    signal,
  });
}

export async function deleteProvider(
  providerId: string | number,
  signal?: AbortSignal,
): Promise<void> {
  return request<void>({
    request: providerManagementApi.deleteProvider,
    pathParams: {
      providerId,
    },
    signal,
  });
}

export async function testProviderConnection(
  providerId: string | number,
  signal?: AbortSignal,
): Promise<ProviderConnectionTestResult> {
  return request<ProviderConnectionTestResult>({
    request: providerManagementApi.testProviderConnection,
    pathParams: {
      providerId,
    },
    signal,
  });
}

export async function fetchProviderRuntimeConfig(
  providerId: string | number,
  modelName?: string,
  signal?: AbortSignal,
): Promise<ProviderRuntimeConfigRecord> {
  return request<ProviderRuntimeConfigRecord>({
    request: providerManagementApi.getRuntimeConfig,
    pathParams: {
      providerId,
    },
    query:
      modelName != null && modelName !== ""
        ? {
            model_name: modelName,
          }
        : undefined,
    signal,
  });
}

export async function invokeProviderTest(
  providerId: string | number,
  payload: ProviderInvokeTestPayload,
  signal?: AbortSignal,
): Promise<ProviderInvokeTestResult> {
  return request<ProviderInvokeTestResult>({
    request: providerManagementApi.invokeProviderTest,
    pathParams: {
      providerId,
    },
    body: payload,
    signal,
  });
}
