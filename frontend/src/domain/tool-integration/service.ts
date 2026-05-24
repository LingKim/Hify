import { toolIntegrationApi } from "@/domain/tool-integration/api";
import type {
  OpenApiPreviewPayload,
  OpenApiPreviewResult,
  ToolDetailRecord,
  ToolExecuteTestPayload,
  ToolExecutionLogListResult,
  ToolExecutionResult,
  ToolFormParameterValue,
  ToolFormValues,
  ToolListQuery,
  ToolListResult,
  ToolOptionRecord,
} from "@/domain/tool-integration/types";
import { request } from "@/shared/api";
import type { QueryParams } from "@/shared/api/types";
import type { ListRequestParams } from "@/shared/types/list";

function parseJsonValue(value: string | undefined, fallback: unknown): unknown {
  const normalized = value?.trim();
  if (normalized === undefined || normalized === "") {
    return fallback;
  }

  try {
    return JSON.parse(normalized) as unknown;
  } catch {
    throw new Error("JSON 配置格式不正确");
  }
}

function parseJsonObject(
  value: string | undefined,
): Record<string, unknown> | null {
  const parsed = parseJsonValue(value, null);
  if (parsed === null) {
    return null;
  }
  if (typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("JSON 配置必须是对象");
  }
  return parsed as Record<string, unknown>;
}

function normalizeParameter(
  parameter: ToolFormParameterValue,
  index: number,
) {
  const enumValues = parseJsonValue(parameter.enumValuesJson, null);
  return {
    name: parameter.name.trim(),
    label: parameter.label.trim() || parameter.name.trim(),
    description: parameter.description?.trim() || null,
    paramLocation: parameter.paramLocation,
    schemaType: parameter.schemaType,
    isRequired: parameter.isRequired,
    defaultValue: parseJsonValue(parameter.defaultValueJson, null),
    enumValues: Array.isArray(enumValues) ? enumValues : null,
    schema: parseJsonObject(parameter.schemaJson) ?? {
      type: parameter.schemaType,
    },
    sortOrder: index,
    metadata: null,
  };
}

function buildToolPayload(values: ToolFormValues) {
  return {
    name: values.name.trim(),
    description: values.description?.trim() || null,
    status: values.status,
    sourceType: values.sourceType,
    httpMethod: values.httpMethod,
    url: values.url.trim(),
    timeoutSeconds: values.timeoutSeconds,
    headersTemplate: parseJsonObject(values.headersTemplateJson),
    queryTemplate: parseJsonObject(values.queryTemplateJson),
    bodyTemplate: parseJsonObject(values.bodyTemplateJson),
    contentType: values.contentType || "application/json",
    auth: {
      authType: values.authType,
      secretValue: values.secretValue?.trim() || null,
      headerName: values.headerName?.trim() || null,
      queryName: values.queryName?.trim() || null,
    },
    parameters: values.parameters.map(normalizeParameter),
    openapiSource: values.openapiSource ?? null,
    metadata: values.metadata ?? null,
  };
}

export async function fetchToolList(
  params: ListRequestParams<ToolListQuery>,
  signal?: AbortSignal,
): Promise<ToolListResult> {
  return request<ToolListResult>({
    request: toolIntegrationApi.listTools,
    query: params as unknown as QueryParams,
    signal,
  });
}

export async function fetchToolOptions(
  query: Pick<ToolListQuery, "keyword" | "status"> = {},
  signal?: AbortSignal,
): Promise<ToolOptionRecord[]> {
  return request<ToolOptionRecord[]>({
    request: toolIntegrationApi.listToolOptions,
    query: query as QueryParams,
    signal,
  });
}

export async function fetchToolDetail(
  toolId: string | number,
  signal?: AbortSignal,
): Promise<ToolDetailRecord> {
  return request<ToolDetailRecord>({
    request: toolIntegrationApi.getToolDetail,
    pathParams: { toolId },
    signal,
  });
}

export async function createTool(
  values: ToolFormValues,
  signal?: AbortSignal,
): Promise<ToolDetailRecord> {
  return request<ToolDetailRecord>({
    request: toolIntegrationApi.createTool,
    body: buildToolPayload(values),
    signal,
  });
}

export async function updateTool(
  toolId: string | number,
  values: ToolFormValues,
  signal?: AbortSignal,
): Promise<ToolDetailRecord> {
  return request<ToolDetailRecord>({
    request: toolIntegrationApi.updateTool,
    pathParams: { toolId },
    body: buildToolPayload(values),
    signal,
  });
}

export async function deleteTool(
  toolId: string | number,
  signal?: AbortSignal,
): Promise<void> {
  return request<void>({
    request: toolIntegrationApi.deleteTool,
    pathParams: { toolId },
    signal,
  });
}

export async function executeToolTest(
  toolId: string | number,
  payload: ToolExecuteTestPayload,
  signal?: AbortSignal,
): Promise<ToolExecutionResult> {
  return request<ToolExecutionResult>({
    request: toolIntegrationApi.executeToolTest,
    pathParams: { toolId },
    body: payload,
    signal,
  });
}

export async function fetchToolExecutionLogs(
  toolId: string | number,
  params: { page: number; pageSize: number; source?: string; status?: string },
  signal?: AbortSignal,
): Promise<ToolExecutionLogListResult> {
  return request<ToolExecutionLogListResult>({
    request: toolIntegrationApi.listExecutionLogs,
    pathParams: { toolId },
    query: params,
    signal,
  });
}

export async function previewOpenApiImport(
  payload: OpenApiPreviewPayload,
  signal?: AbortSignal,
): Promise<OpenApiPreviewResult> {
  return request<OpenApiPreviewResult>({
    request: toolIntegrationApi.previewOpenApiImport,
    body: payload,
    signal,
  });
}
