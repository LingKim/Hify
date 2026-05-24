import {
  mutationOptions,
  queryOptions,
  type QueryClient,
  type UseMutationOptions,
} from "@tanstack/react-query";
import {
  createTool,
  deleteTool,
  executeToolTest,
  fetchToolDetail,
  fetchToolExecutionLogs,
  fetchToolList,
  previewOpenApiImport,
  updateTool,
} from "@/domain/tool-integration/service";
import type {
  OpenApiPreviewPayload,
  OpenApiPreviewResult,
  ToolDetailRecord,
  ToolExecuteTestPayload,
  ToolExecutionResult,
  ToolFormValues,
  ToolListQuery,
} from "@/domain/tool-integration/types";
import type { ListRequestParams } from "@/shared/types/list";

export const toolIntegrationQueryKeys = {
  all: ["tool-integration"] as const,
  list: (params: ListRequestParams<ToolListQuery>) =>
    [...toolIntegrationQueryKeys.all, "list", params] as const,
  detail: (toolId: string | number) =>
    [...toolIntegrationQueryKeys.all, "detail", toolId] as const,
  logs: (
    toolId: string | number,
    params: { page: number; pageSize: number; source?: string; status?: string },
  ) => [...toolIntegrationQueryKeys.all, "logs", toolId, params] as const,
};

type MutationOverride<TData, TVariables> = Omit<
  UseMutationOptions<TData, Error, TVariables, unknown>,
  "mutationFn" | "mutationKey"
>;

export function toolDetailQueryOptions(toolId: string | number) {
  return queryOptions({
    queryKey: toolIntegrationQueryKeys.detail(toolId),
    queryFn: ({ signal }) => fetchToolDetail(toolId, signal),
  });
}

export function toolExecutionLogsQueryOptions(
  toolId: string | number,
  params: { page: number; pageSize: number; source?: string; status?: string },
) {
  return queryOptions({
    queryKey: toolIntegrationQueryKeys.logs(toolId, params),
    queryFn: ({ signal }) => fetchToolExecutionLogs(toolId, params, signal),
    enabled: toolId !== "",
  });
}

export function createToolMutationOptions(
  queryClient: QueryClient,
  overrides?: MutationOverride<ToolDetailRecord, ToolFormValues>,
) {
  return mutationOptions<ToolDetailRecord, Error, ToolFormValues>({
    mutationKey: [...toolIntegrationQueryKeys.all, "create"],
    mutationFn: (values) => createTool(values),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({
        queryKey: toolIntegrationQueryKeys.all,
      });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function updateToolMutationOptions(
  queryClient: QueryClient,
  toolId: string | number,
  overrides?: MutationOverride<ToolDetailRecord, ToolFormValues>,
) {
  return mutationOptions<ToolDetailRecord, Error, ToolFormValues>({
    mutationKey: [...toolIntegrationQueryKeys.all, "update", toolId],
    mutationFn: (values) => updateTool(toolId, values),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({
        queryKey: toolIntegrationQueryKeys.all,
      });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function deleteToolMutationOptions(
  queryClient: QueryClient,
  overrides?: MutationOverride<void, string | number>,
) {
  return mutationOptions<void, Error, string | number>({
    mutationKey: [...toolIntegrationQueryKeys.all, "delete"],
    mutationFn: (toolId) => deleteTool(toolId),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({
        queryKey: toolIntegrationQueryKeys.all,
      });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function executeToolTestMutationOptions(
  queryClient: QueryClient,
  toolId: string | number,
  overrides?: MutationOverride<ToolExecutionResult, ToolExecuteTestPayload>,
) {
  return mutationOptions<ToolExecutionResult, Error, ToolExecuteTestPayload>({
    mutationKey: [...toolIntegrationQueryKeys.all, "execute-test", toolId],
    mutationFn: (payload) => executeToolTest(toolId, payload),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({
        queryKey: toolIntegrationQueryKeys.all,
      });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function previewOpenApiMutationOptions(
  overrides?: MutationOverride<OpenApiPreviewResult, OpenApiPreviewPayload>,
) {
  return mutationOptions<OpenApiPreviewResult, Error, OpenApiPreviewPayload>({
    mutationKey: [...toolIntegrationQueryKeys.all, "openapi-preview"],
    mutationFn: (payload) => previewOpenApiImport(payload),
    ...overrides,
  });
}

export { fetchToolList };
