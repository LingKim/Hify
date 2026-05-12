import { mutationOptions, queryOptions } from "@tanstack/react-query";
import { fetchCurrentUser, login } from "@/domain/auth/service";

export const authQueryKeys = {
  all: ["auth"] as const,
  currentUser: () => [...authQueryKeys.all, "me"] as const,
};

export function currentUserQueryOptions(enabled: boolean) {
  return queryOptions({
    queryKey: authQueryKeys.currentUser(),
    queryFn: ({ signal }) => fetchCurrentUser(signal),
    enabled,
    retry: false,
    staleTime: 60_000,
  });
}

export function loginMutationOptions() {
  return mutationOptions({
    mutationKey: [...authQueryKeys.all, "login"],
    mutationFn: login,
  });
}
