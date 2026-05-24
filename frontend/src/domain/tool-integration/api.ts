export const toolIntegrationApi = {
  listTools: "GET /tools",
  listToolOptions: "GET /tools/options",
  createTool: "POST /tools",
  getToolDetail: "GET /tools/{toolId}",
  updateTool: "PUT /tools/{toolId}",
  deleteTool: "DELETE /tools/{toolId}",
  executeToolTest: "POST /tools/{toolId}/execute-test",
  listExecutionLogs: "GET /tools/{toolId}/execution-logs",
  previewOpenApiImport: "POST /tools/import-openapi/preview",
} as const;
