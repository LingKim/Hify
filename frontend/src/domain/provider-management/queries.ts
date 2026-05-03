import {
  mutationOptions,
  queryOptions,
  type QueryClient,
  type UseMutationOptions,
} from "@tanstack/react-query";
import {
  createProvider,
  deleteProvider,
  fetchProviderDetail,
  fetchProviderList,
  invokeProviderTest,
  testProviderConnection,
  updateProvider,
} from "@/domain/provider-management/service";
import type {
  ProviderConnectionTestResult,
  ProviderDetailRecord,
  ProviderFormValues,
  ProviderInvokeTestPayload,
  ProviderInvokeTestResult,
  ProviderListQuery,
} from "@/domain/provider-management/types";
import type { ListRequestParams } from "@/shared/types/list";

export const providerManagementQueryKeys = {
  all: ["provider-management"] as const,
  list: (params: ListRequestParams<ProviderListQuery>) =>
    [...providerManagementQueryKeys.all, "list", params] as const,
  detail: (providerId: string | number) =>
    [...providerManagementQueryKeys.all, "detail", providerId] as const,
};

type MutationOverride<TData, TVariables> = Omit<
  UseMutationOptions<TData, Error, TVariables, unknown>,
  "mutationFn" | "mutationKey"
>;

export function providerDetailQueryOptions(providerId: string | number) {
  return queryOptions({
    queryKey: providerManagementQueryKeys.detail(providerId),
    queryFn: ({ signal }) => fetchProviderDetail(providerId, signal),
  });
}

export function createProviderMutationOptions(
  queryClient: QueryClient,
  overrides?: MutationOverride<ProviderDetailRecord, ProviderFormValues>,
) {
  return mutationOptions<ProviderDetailRecord, Error, ProviderFormValues>({
    mutationKey: [...providerManagementQueryKeys.all, "create"],
    mutationFn: (values) => createProvider(values),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({
        queryKey: providerManagementQueryKeys.all,
      });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function updateProviderMutationOptions(
  queryClient: QueryClient,
  providerId: string | number,
  overrides?: MutationOverride<ProviderDetailRecord, ProviderFormValues>,
) {
  return mutationOptions<ProviderDetailRecord, Error, ProviderFormValues>({
    mutationKey: [...providerManagementQueryKeys.all, "update", providerId],
    mutationFn: (values) => updateProvider(providerId, values),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({
        queryKey: providerManagementQueryKeys.all,
      });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function deleteProviderMutationOptions(
  queryClient: QueryClient,
  overrides?: MutationOverride<void, string | number>,
) {
  return mutationOptions<void, Error, string | number>({
    mutationKey: [...providerManagementQueryKeys.all, "delete"],
    mutationFn: (providerId) => deleteProvider(providerId),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({
        queryKey: providerManagementQueryKeys.all,
      });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function testProviderConnectionMutationOptions(
  queryClient: QueryClient,
  overrides?: MutationOverride<ProviderConnectionTestResult, string | number>,
) {
  return mutationOptions<
    ProviderConnectionTestResult,
    Error,
    string | number
  >({
    mutationKey: [...providerManagementQueryKeys.all, "test-connection"],
    mutationFn: (providerId) => testProviderConnection(providerId),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({
        queryKey: providerManagementQueryKeys.all,
      });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function invokeProviderTestMutationOptions(
  queryClient: QueryClient,
  providerId: string | number,
  overrides?: MutationOverride<ProviderInvokeTestResult, ProviderInvokeTestPayload>,
) {
  return mutationOptions<
    ProviderInvokeTestResult,
    Error,
    ProviderInvokeTestPayload
  >({
    mutationKey: [...providerManagementQueryKeys.all, "invoke-test", providerId],
    mutationFn: (payload) => invokeProviderTest(providerId, payload),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({
        queryKey: providerManagementQueryKeys.all,
      });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export { fetchProviderList };
