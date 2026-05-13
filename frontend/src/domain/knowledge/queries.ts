import {
  mutationOptions,
  queryOptions,
  type QueryClient,
  type UseMutationOptions,
} from "@tanstack/react-query";
import {
  createKnowledgeBase,
  deleteKnowledgeBase,
  deleteKnowledgeDocument,
  fetchKnowledgeBaseDetail,
  fetchKnowledgeBaseList,
  fetchKnowledgeDocuments,
  reprocessKnowledgeDocument,
  runRetrievalTest,
  updateKnowledgeBase,
  uploadKnowledgeDocument,
} from "@/domain/knowledge/service";
import type {
  KnowledgeBaseDetail,
  KnowledgeBaseFormValues,
  KnowledgeBaseListQuery,
  KnowledgeDocumentListResult,
  KnowledgeDocumentQuery,
  KnowledgeDocumentRecord,
  RetrievalTestPayload,
  RetrievalTestResult,
} from "@/domain/knowledge/types";
import type { ListRequestParams } from "@/shared/types/list";

export const knowledgeQueryKeys = {
  all: ["knowledge"] as const,
  list: (params: ListRequestParams<KnowledgeBaseListQuery>) =>
    [...knowledgeQueryKeys.all, "list", params] as const,
  detail: (knowledgeBaseId: string | number) =>
    [...knowledgeQueryKeys.all, "detail", knowledgeBaseId] as const,
  documents: (
    knowledgeBaseId: string | number,
    params: ListRequestParams<KnowledgeDocumentQuery>,
  ) => [...knowledgeQueryKeys.all, "documents", knowledgeBaseId, params] as const,
};

type MutationOverride<TData, TVariables> = Omit<
  UseMutationOptions<TData, Error, TVariables, unknown>,
  "mutationFn" | "mutationKey"
>;

export function knowledgeBaseListQueryOptions(
  params: ListRequestParams<KnowledgeBaseListQuery>,
) {
  return queryOptions({
    queryKey: knowledgeQueryKeys.list(params),
    queryFn: ({ signal }) => fetchKnowledgeBaseList(params, signal),
  });
}

export function knowledgeBaseDetailQueryOptions(
  knowledgeBaseId: string | number,
) {
  return queryOptions({
    queryKey: knowledgeQueryKeys.detail(knowledgeBaseId),
    queryFn: ({ signal }) => fetchKnowledgeBaseDetail(knowledgeBaseId, signal),
    enabled: knowledgeBaseId !== "",
  });
}

export function knowledgeDocumentsQueryOptions(
  knowledgeBaseId: string | number,
  params: ListRequestParams<KnowledgeDocumentQuery>,
) {
  return queryOptions<KnowledgeDocumentListResult>({
    queryKey: knowledgeQueryKeys.documents(knowledgeBaseId, params),
    queryFn: ({ signal }) =>
      fetchKnowledgeDocuments(knowledgeBaseId, params, signal),
    enabled: knowledgeBaseId !== "",
  });
}

export function createKnowledgeBaseMutationOptions(
  queryClient: QueryClient,
  overrides?: MutationOverride<KnowledgeBaseDetail, KnowledgeBaseFormValues>,
) {
  return mutationOptions<KnowledgeBaseDetail, Error, KnowledgeBaseFormValues>({
    mutationKey: [...knowledgeQueryKeys.all, "create"],
    mutationFn: (values) => createKnowledgeBase(values),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({ queryKey: knowledgeQueryKeys.all });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function updateKnowledgeBaseMutationOptions(
  queryClient: QueryClient,
  knowledgeBaseId: string | number,
  overrides?: MutationOverride<KnowledgeBaseDetail, KnowledgeBaseFormValues>,
) {
  return mutationOptions<KnowledgeBaseDetail, Error, KnowledgeBaseFormValues>({
    mutationKey: [...knowledgeQueryKeys.all, "update", knowledgeBaseId],
    mutationFn: (values) => updateKnowledgeBase(knowledgeBaseId, values),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({ queryKey: knowledgeQueryKeys.all });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function deleteKnowledgeBaseMutationOptions(
  queryClient: QueryClient,
  overrides?: MutationOverride<void, string | number>,
) {
  return mutationOptions<void, Error, string | number>({
    mutationKey: [...knowledgeQueryKeys.all, "delete"],
    mutationFn: (knowledgeBaseId) => deleteKnowledgeBase(knowledgeBaseId),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({ queryKey: knowledgeQueryKeys.all });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function uploadKnowledgeDocumentMutationOptions(
  queryClient: QueryClient,
  knowledgeBaseId: string | number,
  overrides?: MutationOverride<KnowledgeDocumentRecord, File>,
) {
  return mutationOptions<KnowledgeDocumentRecord, Error, File>({
    mutationKey: [...knowledgeQueryKeys.all, "upload", knowledgeBaseId],
    mutationFn: (file) => uploadKnowledgeDocument(knowledgeBaseId, file),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({ queryKey: knowledgeQueryKeys.all });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function deleteKnowledgeDocumentMutationOptions(
  queryClient: QueryClient,
  knowledgeBaseId: string | number,
  overrides?: MutationOverride<void, string | number>,
) {
  return mutationOptions<void, Error, string | number>({
    mutationKey: [...knowledgeQueryKeys.all, "delete-document", knowledgeBaseId],
    mutationFn: (documentId) =>
      deleteKnowledgeDocument(knowledgeBaseId, documentId),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({ queryKey: knowledgeQueryKeys.all });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function reprocessKnowledgeDocumentMutationOptions(
  queryClient: QueryClient,
  knowledgeBaseId: string | number,
  overrides?: MutationOverride<KnowledgeDocumentRecord, string | number>,
) {
  return mutationOptions<KnowledgeDocumentRecord, Error, string | number>({
    mutationKey: [...knowledgeQueryKeys.all, "reprocess", knowledgeBaseId],
    mutationFn: (documentId) =>
      reprocessKnowledgeDocument(knowledgeBaseId, documentId),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({ queryKey: knowledgeQueryKeys.all });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function retrievalTestMutationOptions(
  knowledgeBaseId: string | number,
  overrides?: MutationOverride<RetrievalTestResult, RetrievalTestPayload>,
) {
  return mutationOptions<RetrievalTestResult, Error, RetrievalTestPayload>({
    mutationKey: [...knowledgeQueryKeys.all, "retrieval-test", knowledgeBaseId],
    mutationFn: (payload) => runRetrievalTest(knowledgeBaseId, payload),
    ...overrides,
  });
}
