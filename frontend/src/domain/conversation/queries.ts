import {
  mutationOptions,
  queryOptions,
  type QueryClient,
  type UseMutationOptions,
} from "@tanstack/react-query";
import {
  createConversation,
  deleteConversation,
  fetchAgentRuntimePreview,
  fetchConversationDetail,
  fetchConversationList,
  fetchConversationMessages,
  updateConversation,
} from "@/domain/conversation/service";
import type {
  ConversationAgentRuntimePreview,
  ConversationCreateValues,
  ConversationDetailRecord,
  ConversationListQuery,
  ConversationMessageQuery,
  ConversationUpdateValues,
} from "@/domain/conversation/types";
import type { ListRequestParams } from "@/shared/types/list";

export const conversationQueryKeys = {
  all: ["conversation"] as const,
  list: (params: ListRequestParams<ConversationListQuery>) =>
    [...conversationQueryKeys.all, "list", params] as const,
  detail: (conversationId: string | number) =>
    [...conversationQueryKeys.all, "detail", conversationId] as const,
  messages: (
    conversationId: string | number,
    params: ListRequestParams<ConversationMessageQuery>,
  ) => [...conversationQueryKeys.all, "messages", conversationId, params] as const,
  runtimePreview: (agentId: string | number) =>
    [...conversationQueryKeys.all, "runtime-preview", agentId] as const,
};

type MutationOverride<TData, TVariables> = Omit<
  UseMutationOptions<TData, Error, TVariables, unknown>,
  "mutationFn" | "mutationKey"
>;

export function conversationDetailQueryOptions(
  conversationId: string | number,
) {
  return queryOptions({
    queryKey: conversationQueryKeys.detail(conversationId),
    queryFn: ({ signal }) => fetchConversationDetail(conversationId, signal),
    enabled: conversationId !== "",
  });
}

export function conversationMessagesQueryOptions(
  conversationId: string | number,
  params: ListRequestParams<ConversationMessageQuery>,
) {
  return queryOptions({
    queryKey: conversationQueryKeys.messages(conversationId, params),
    queryFn: ({ signal }) =>
      fetchConversationMessages(conversationId, params, signal),
    enabled: conversationId !== "",
  });
}

export function agentRuntimePreviewQueryOptions(agentId: string | number) {
  return queryOptions<ConversationAgentRuntimePreview>({
    queryKey: conversationQueryKeys.runtimePreview(agentId),
    queryFn: ({ signal }) => fetchAgentRuntimePreview(agentId, signal),
    enabled: agentId !== "",
  });
}

export function createConversationMutationOptions(
  queryClient: QueryClient,
  overrides?: MutationOverride<ConversationDetailRecord, ConversationCreateValues>,
) {
  return mutationOptions<
    ConversationDetailRecord,
    Error,
    ConversationCreateValues
  >({
    mutationKey: [...conversationQueryKeys.all, "create"],
    mutationFn: (values) => createConversation(values),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({
        queryKey: conversationQueryKeys.all,
      });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function updateConversationMutationOptions(
  queryClient: QueryClient,
  conversationId: string | number,
  overrides?: MutationOverride<ConversationDetailRecord, ConversationUpdateValues>,
) {
  return mutationOptions<
    ConversationDetailRecord,
    Error,
    ConversationUpdateValues
  >({
    mutationKey: [...conversationQueryKeys.all, "update", conversationId],
    mutationFn: (values) => updateConversation(conversationId, values),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({
        queryKey: conversationQueryKeys.all,
      });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function deleteConversationMutationOptions(
  queryClient: QueryClient,
  overrides?: MutationOverride<void, string | number>,
) {
  return mutationOptions<void, Error, string | number>({
    mutationKey: [...conversationQueryKeys.all, "delete"],
    mutationFn: (conversationId) => deleteConversation(conversationId),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({
        queryKey: conversationQueryKeys.all,
      });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export { fetchConversationList };
