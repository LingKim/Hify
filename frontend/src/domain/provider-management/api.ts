export const providerManagementApi = {
  listProviders: "GET /llms/providers",
  getProviderDetail: "GET /llms/providers/{providerId}",
  createProvider: "POST /llms/providers",
  updateProvider: "PUT /llms/providers/{providerId}",
  deleteProvider: "DELETE /llms/providers/{providerId}",
  testProviderConnection: "POST /llms/providers/{providerId}/test-connection",
  invokeProviderTest: "POST /llms/providers/{providerId}/invoke-test",
  getRuntimeConfig: "GET /llms/providers/{providerId}/runtime-config",
} as const;
