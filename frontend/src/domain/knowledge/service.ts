import { knowledgeApi } from "@/domain/knowledge/api";
import type {
  KnowledgeBaseDetail,
  KnowledgeBaseFormValues,
  KnowledgeBaseListQuery,
  KnowledgeBaseListResult,
  KnowledgeBaseOption,
  KnowledgeDocumentListResult,
  KnowledgeDocumentQuery,
  KnowledgeDocumentRecord,
  RetrievalTestPayload,
  RetrievalTestResult,
} from "@/domain/knowledge/types";
import { request } from "@/shared/api";
import type { QueryParams } from "@/shared/api/types";
import type { ListRequestParams } from "@/shared/types/list";

function buildKnowledgeBasePayload(values: KnowledgeBaseFormValues) {
  return {
    name: values.name,
    description: values.description?.trim() || null,
    status: values.status,
    visibility: values.visibility,
    chunkSize: values.chunkSize,
    chunkOverlap: values.chunkOverlap,
    defaultTopK: values.defaultTopK,
    defaultScoreThreshold: values.defaultScoreThreshold,
    metadata: null,
  };
}

export async function fetchKnowledgeBaseList(
  params: ListRequestParams<KnowledgeBaseListQuery>,
  signal?: AbortSignal,
): Promise<KnowledgeBaseListResult> {
  return request<KnowledgeBaseListResult>({
    request: knowledgeApi.listKnowledgeBases,
    query: params as unknown as QueryParams,
    signal,
  });
}

export async function fetchKnowledgeBaseDetail(
  knowledgeBaseId: string | number,
  signal?: AbortSignal,
): Promise<KnowledgeBaseDetail> {
  return request<KnowledgeBaseDetail>({
    request: knowledgeApi.getKnowledgeBase,
    pathParams: { knowledgeBaseId },
    signal,
  });
}

export async function fetchKnowledgeBaseOptions(
  signal?: AbortSignal,
): Promise<KnowledgeBaseOption[]> {
  return request<KnowledgeBaseOption[]>({
    request: knowledgeApi.listOptions,
    query: { status_value: "enabled" },
    signal,
  });
}

export async function createKnowledgeBase(
  values: KnowledgeBaseFormValues,
  signal?: AbortSignal,
): Promise<KnowledgeBaseDetail> {
  return request<KnowledgeBaseDetail>({
    request: knowledgeApi.createKnowledgeBase,
    body: buildKnowledgeBasePayload(values),
    signal,
  });
}

export async function updateKnowledgeBase(
  knowledgeBaseId: string | number,
  values: KnowledgeBaseFormValues,
  signal?: AbortSignal,
): Promise<KnowledgeBaseDetail> {
  return request<KnowledgeBaseDetail>({
    request: knowledgeApi.updateKnowledgeBase,
    pathParams: { knowledgeBaseId },
    body: buildKnowledgeBasePayload(values),
    signal,
  });
}

export async function deleteKnowledgeBase(
  knowledgeBaseId: string | number,
  signal?: AbortSignal,
): Promise<void> {
  return request<void>({
    request: knowledgeApi.deleteKnowledgeBase,
    pathParams: { knowledgeBaseId },
    signal,
  });
}

export async function fetchKnowledgeDocuments(
  knowledgeBaseId: string | number,
  params: ListRequestParams<KnowledgeDocumentQuery>,
  signal?: AbortSignal,
): Promise<KnowledgeDocumentListResult> {
  return request<KnowledgeDocumentListResult>({
    request: knowledgeApi.listDocuments,
    pathParams: { knowledgeBaseId },
    query: params as unknown as QueryParams,
    signal,
  });
}

export async function uploadKnowledgeDocument(
  knowledgeBaseId: string | number,
  file: File,
  signal?: AbortSignal,
): Promise<KnowledgeDocumentRecord> {
  const formData = new FormData();
  formData.append("file", file);
  return request<KnowledgeDocumentRecord>({
    request: knowledgeApi.uploadDocument,
    pathParams: { knowledgeBaseId },
    body: formData,
    signal,
  });
}

export async function deleteKnowledgeDocument(
  knowledgeBaseId: string | number,
  documentId: string | number,
  signal?: AbortSignal,
): Promise<void> {
  return request<void>({
    request: knowledgeApi.deleteDocument,
    pathParams: { knowledgeBaseId, documentId },
    signal,
  });
}

export async function reprocessKnowledgeDocument(
  knowledgeBaseId: string | number,
  documentId: string | number,
  signal?: AbortSignal,
): Promise<KnowledgeDocumentRecord> {
  return request<KnowledgeDocumentRecord>({
    request: knowledgeApi.reprocessDocument,
    pathParams: { knowledgeBaseId, documentId },
    signal,
  });
}

export async function runRetrievalTest(
  knowledgeBaseId: string | number,
  payload: RetrievalTestPayload,
  signal?: AbortSignal,
): Promise<RetrievalTestResult> {
  return request<RetrievalTestResult>({
    request: knowledgeApi.retrievalTest,
    pathParams: { knowledgeBaseId },
    body: payload,
    signal,
  });
}
