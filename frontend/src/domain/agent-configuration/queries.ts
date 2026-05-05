import {
  mutationOptions,
  queryOptions,
  type QueryClient,
  type UseMutationOptions,
} from "@tanstack/react-query";
import {
  createAgent,
  deleteAgent,
  fetchAgentConfigPreview,
  fetchAgentDetail,
  fetchAgentList,
  updateAgent,
} from "@/domain/agent-configuration/service";
import type {
  AgentConfigPreviewRecord,
  AgentDetailRecord,
  AgentFormValues,
  AgentListQuery,
} from "@/domain/agent-configuration/types";
import type { ListRequestParams } from "@/shared/types/list";

export const agentConfigurationQueryKeys = {
  all: ["agent-configuration"] as const,
  list: (params: ListRequestParams<AgentListQuery>) =>
    [...agentConfigurationQueryKeys.all, "list", params] as const,
  detail: (agentId: string | number) =>
    [...agentConfigurationQueryKeys.all, "detail", agentId] as const,
  preview: (agentId: string | number) =>
    [...agentConfigurationQueryKeys.all, "preview", agentId] as const,
};

type MutationOverride<TData, TVariables> = Omit<
  UseMutationOptions<TData, Error, TVariables, unknown>,
  "mutationFn" | "mutationKey"
>;

export function agentDetailQueryOptions(agentId: string | number) {
  return queryOptions({
    queryKey: agentConfigurationQueryKeys.detail(agentId),
    queryFn: ({ signal }) => fetchAgentDetail(agentId, signal),
  });
}

export function agentConfigPreviewQueryOptions(agentId: string | number) {
  return queryOptions({
    queryKey: agentConfigurationQueryKeys.preview(agentId),
    queryFn: ({ signal }) => fetchAgentConfigPreview(agentId, signal),
  });
}

export function createAgentMutationOptions(
  queryClient: QueryClient,
  overrides?: MutationOverride<AgentDetailRecord, AgentFormValues>,
) {
  return mutationOptions<AgentDetailRecord, Error, AgentFormValues>({
    mutationKey: [...agentConfigurationQueryKeys.all, "create"],
    mutationFn: (values) => createAgent(values),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({
        queryKey: agentConfigurationQueryKeys.all,
      });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function updateAgentMutationOptions(
  queryClient: QueryClient,
  agentId: string | number,
  overrides?: MutationOverride<AgentDetailRecord, AgentFormValues>,
) {
  return mutationOptions<AgentDetailRecord, Error, AgentFormValues>({
    mutationKey: [...agentConfigurationQueryKeys.all, "update", agentId],
    mutationFn: (values) => updateAgent(agentId, values),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({
        queryKey: agentConfigurationQueryKeys.all,
      });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function deleteAgentMutationOptions(
  queryClient: QueryClient,
  overrides?: MutationOverride<void, string | number>,
) {
  return mutationOptions<void, Error, string | number>({
    mutationKey: [...agentConfigurationQueryKeys.all, "delete"],
    mutationFn: (agentId) => deleteAgent(agentId),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({
        queryKey: agentConfigurationQueryKeys.all,
      });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export { fetchAgentConfigPreview, fetchAgentList };
export type { AgentConfigPreviewRecord };
