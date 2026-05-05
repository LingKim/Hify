export const agentConfigurationApi = {
  listAgents: "GET /agents",
  getAgentDetail: "GET /agents/{agentId}",
  createAgent: "POST /agents",
  updateAgent: "PUT /agents/{agentId}",
  deleteAgent: "DELETE /agents/{agentId}",
  getAgentConfigPreview: "GET /agents/{agentId}/config-preview",
} as const;
