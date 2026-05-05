export const conversationApi = {
  listConversations: "GET /conversations",
  createConversation: "POST /conversations",
  getConversation: "GET /conversations/{conversationId}",
  updateConversation: "PATCH /conversations/{conversationId}",
  deleteConversation: "DELETE /conversations/{conversationId}",
  listMessages: "GET /conversations/{conversationId}/messages",
  streamMessage: "POST /conversations/{conversationId}/messages/stream",
  getAgentRuntimePreview: "GET /conversations/agents/{agentId}/runtime-preview",
} as const;
