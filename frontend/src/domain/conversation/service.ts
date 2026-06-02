import { conversationApi } from "@/domain/conversation/api";
import type {
  ConversationAgentRuntimePreview,
  ConversationCreateValues,
  ConversationDetailRecord,
  ConversationListQuery,
  ConversationListResult,
  ConversationMessageListResult,
  ConversationMessageQuery,
  ConversationUpdateValues,
  StreamMessageCallbacks,
} from "@/domain/conversation/types";
import { AppBusinessError, AppRequestError, request } from "@/shared/api";
import { getApiBasePath } from "@/shared/config/env";
import { getAccessToken } from "@/shared/auth/token";
import type { QueryParams } from "@/shared/api/types";
import type { ListRequestParams } from "@/shared/types/list";

export async function fetchConversationList(
  params: ListRequestParams<ConversationListQuery>,
  signal?: AbortSignal,
): Promise<ConversationListResult> {
  return request<ConversationListResult>({
    request: conversationApi.listConversations,
    query: params as unknown as QueryParams,
    signal,
  });
}

export async function createConversation(
  values: ConversationCreateValues,
  signal?: AbortSignal,
): Promise<ConversationDetailRecord> {
  return request<ConversationDetailRecord>({
    request: conversationApi.createConversation,
    body: {
      agentId: values.agentId,
      title: values.title?.trim() || undefined,
      channel: values.channel ?? "web",
      metadata: values.metadata ?? null,
    },
    signal,
  });
}

export async function fetchConversationDetail(
  conversationId: string | number,
  signal?: AbortSignal,
): Promise<ConversationDetailRecord> {
  return request<ConversationDetailRecord>({
    request: conversationApi.getConversation,
    pathParams: { conversationId },
    signal,
  });
}

export async function updateConversation(
  conversationId: string | number,
  values: ConversationUpdateValues,
  signal?: AbortSignal,
): Promise<ConversationDetailRecord> {
  return request<ConversationDetailRecord>({
    request: conversationApi.updateConversation,
    pathParams: { conversationId },
    body: values,
    signal,
  });
}

export async function deleteConversation(
  conversationId: string | number,
  signal?: AbortSignal,
): Promise<void> {
  return request<void>({
    request: conversationApi.deleteConversation,
    pathParams: { conversationId },
    signal,
  });
}

export async function fetchConversationMessages(
  conversationId: string | number,
  params: ListRequestParams<ConversationMessageQuery>,
  signal?: AbortSignal,
): Promise<ConversationMessageListResult> {
  return request<ConversationMessageListResult>({
    request: conversationApi.listMessages,
    pathParams: { conversationId },
    query: params as unknown as QueryParams,
    signal,
  });
}

export async function fetchAgentRuntimePreview(
  agentId: string | number,
  signal?: AbortSignal,
): Promise<ConversationAgentRuntimePreview> {
  return request<ConversationAgentRuntimePreview>({
    request: conversationApi.getAgentRuntimePreview,
    pathParams: { agentId },
    signal,
  });
}

export async function streamConversationMessage(
  conversationId: string | number,
  content: string,
  callbacks: StreamMessageCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  const headers = new Headers({
    Accept: "text/event-stream",
    "Content-Type": "application/json",
  });
  const accessToken = getAccessToken();
  if (accessToken !== null && accessToken !== "") {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const response = await fetch(
    `${getApiBasePath()}/conversations/${conversationId}/messages/stream`,
    {
      method: "POST",
      headers,
      body: JSON.stringify({ content }),
      signal,
    },
  );

  if (!response.ok) {
    await throwJsonError(response);
  }

  if (response.body == null) {
    throw new AppRequestError("后端没有返回可读取的 SSE 数据流");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split(/\n\n/);
    buffer = blocks.pop() ?? "";

    blocks.forEach((block) => dispatchSseBlock(block, callbacks));
  }

  if (buffer.trim() !== "") {
    dispatchSseBlock(buffer, callbacks);
  }
}

async function throwJsonError(response: Response): Promise<never> {
  try {
    const payload = (await response.json()) as {
      code?: number;
      message?: string;
    };
    throw new AppBusinessError(
      payload.message ?? "请求失败",
      payload.code ?? response.status,
      response.status,
    );
  } catch (error) {
    if (error instanceof AppBusinessError) {
      throw error;
    }
    throw new AppRequestError("SSE 建连失败");
  }
}

function dispatchSseBlock(
  block: string,
  callbacks: StreamMessageCallbacks,
): void {
  const lines = block.split(/\n/);
  const eventLine = lines.find((line) => line.startsWith("event:"));
  const dataLines = lines.filter((line) => line.startsWith("data:"));
  const event = eventLine?.slice("event:".length).trim();
  const dataText = dataLines
    .map((line) => line.slice("data:".length).trim())
    .join("\n");

  if (event === undefined || dataText === "") {
    return;
  }

  const data = JSON.parse(dataText) as unknown;

  switch (event) {
    case "run.started":
      callbacks.onRunStarted?.(data as never);
      break;
    case "message.created":
      callbacks.onMessageCreated?.(data as never);
      break;
    case "tool.started":
      callbacks.onToolStarted?.(data as never);
      break;
    case "tool.completed":
      callbacks.onToolCompleted?.(data as never);
      break;
    case "tool.failed":
      callbacks.onToolFailed?.(data as never);
      break;
    case "message.delta":
      callbacks.onDelta?.(data as never);
      break;
    case "message.completed":
      callbacks.onMessageCompleted?.(data as never);
      break;
    case "run.completed":
      callbacks.onRunCompleted?.(data as never);
      break;
    case "done":
      callbacks.onDone?.(data as never);
      break;
    case "error":
      callbacks.onError?.(data as never);
      break;
    default:
      break;
  }
}
