import {
  mutationOptions,
  queryOptions,
  useQuery,
  type MutationFunction,
  type QueryClient,
  type UseMutationOptions,
} from "@tanstack/react-query";
import { fetchHealthSnapshot } from "@/domain/health/service";

export const healthQueryKeys = {
  all: ["health"] as const,
  snapshot: () => [...healthQueryKeys.all, "snapshot"] as const,
};

export function healthSnapshotQueryOptions() {
  return queryOptions({
    queryKey: healthQueryKeys.snapshot(),
    queryFn: ({ signal }) => fetchHealthSnapshot(signal),
  });
}

export function useHealthQuery() {
  return useQuery(healthSnapshotQueryOptions());
}

type MutationOverride<TData, TVariables> = Omit<
  UseMutationOptions<TData, Error, TVariables, unknown>,
  "mutationFn" | "mutationKey"
>;

export function createHealthMutationOptions<TData, TVariables>(
  queryClient: QueryClient,
  mutationFn: MutationFunction<TData, TVariables>,
  overrides?: MutationOverride<TData, TVariables>,
) {
  return mutationOptions<TData, Error, TVariables>({
    mutationKey: [...healthQueryKeys.all, "mutation"],
    mutationFn,
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({
        queryKey: healthQueryKeys.all,
      });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}
