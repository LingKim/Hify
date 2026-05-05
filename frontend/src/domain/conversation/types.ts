import type { AgentStatus } from "@/domain/agent-configuration/types";
import type { PageResult } from "@/shared/types/list";

export type ConversationStatus = "active" | "archived";
export type ConversationMessageRole = "user" | "assistant" | "system" | "tool";
export type ConversationMessageStatus =
  | "pending"
  | "streaming"
  | "completed"
  | "failed"
  | "cancelled";
export type ConversationStreamState =
  | "idle"
  | "creatingConversation"
  | "connecting"
  | "streaming"
  | "completed"
  | "failed";

export interface ConversationListQuery {
  keyword?: string;
  agentId?: number;
  status?: ConversationStatus;
  includeArchived?: boolean;
}

export interface ConversationRecord {
  id: number;
  userId: number;
  agentId: number;
  agentName: string;
  title: string;
  status: ConversationStatus;
  channel: string;
  lastMessageRole: string | null;
  lastMessagePreview: string | null;
  lastMessageAt: string | null;
  messageCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface ConversationDetailRecord extends ConversationRecord {
  openingMessage: string | null;
  agentSnapshot: Record<string, unknown>;
  metadata: Record<string, unknown> | null;
}

export interface ConversationCreateValues {
  agentId: number;
  title?: string;
  channel?: string;
  metadata?: Record<string, unknown> | null;
}

export interface ConversationUpdateValues {
  title?: string;
  status?: ConversationStatus;
}

export interface ConversationMessageQuery {
  role?: ConversationMessageRole;
}

export interface ConversationMessageRecord {
  id: number | string;
  conversationId: number;
  runId: number | null;
  role: ConversationMessageRole;
  status: ConversationMessageStatus;
  content: string;
  contentFormat: string;
  sequence: number;
  tokenCount: number | null;
  latencyMs: number | null;
  modelSnapshot: Record<string, unknown> | null;
  error: Record<string, unknown> | null;
  createdAt: string;
  updatedAt: string;
  isLocal?: boolean;
}

export interface ConversationRuntimeModel {
  providerInstanceId: number;
  providerName: string | null;
  providerType: string | null;
  modelId: number;
  modelName: string;
  displayName: string;
  supportsStream: boolean;
}

export interface ConversationAgentRuntimePreview {
  agentId: number;
  name: string;
  status: AgentStatus;
  orchestrationMode: string;
  isRunnable: boolean;
  blockedReason: string | null;
  model: ConversationRuntimeModel | null;
  openingMessage: string | null;
  enabledToolIds: number[];
  enabledKnowledgeBaseIds: number[];
}

export interface StreamRunStartedEvent {
  runId: number;
  conversationId: number;
  status: string;
  startedAt: string | null;
}

export interface StreamMessageCreatedEvent {
  userMessage: Partial<ConversationMessageRecord> & {
    id: number;
    role: ConversationMessageRole;
    status: ConversationMessageStatus;
    content: string;
    sequence: number;
    createdAt: string;
  };
  assistantMessage: Partial<ConversationMessageRecord> & {
    id: number;
    role: ConversationMessageRole;
    status: ConversationMessageStatus;
    content: string;
    sequence: number;
    createdAt: string;
  };
}

export interface StreamDeltaEvent {
  runId: number;
  messageId: number;
  delta: string;
  sequence: number;
}

export interface StreamMessageCompletedEvent {
  runId: number;
  message: Partial<ConversationMessageRecord> & {
    id: number;
    role: ConversationMessageRole;
    status: ConversationMessageStatus;
    content: string;
    sequence: number;
  };
}

export interface StreamRunCompletedEvent {
  runId: number;
  status: string;
}

export interface StreamDoneEvent {
  runId: number;
  conversationId: number;
}

export interface StreamErrorEvent {
  runId?: number;
  messageId?: number;
  code: number;
  message: string;
  status: "failed";
  retryable: boolean;
}

export interface StreamMessageCallbacks {
  onRunStarted?: (event: StreamRunStartedEvent) => void;
  onMessageCreated?: (event: StreamMessageCreatedEvent) => void;
  onDelta?: (event: StreamDeltaEvent) => void;
  onMessageCompleted?: (event: StreamMessageCompletedEvent) => void;
  onRunCompleted?: (event: StreamRunCompletedEvent) => void;
  onDone?: (event: StreamDoneEvent) => void;
  onError?: (event: StreamErrorEvent) => void;
}

export type ConversationListResult = PageResult<ConversationRecord>;
export type ConversationMessageListResult = PageResult<ConversationMessageRecord>;
