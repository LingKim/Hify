import {
  mutationOptions,
  queryOptions,
  type QueryClient,
  type UseMutationOptions,
} from "@tanstack/react-query";
import {
  createUser,
  deleteUser,
  disableUser,
  enableUser,
  fetchUserDetail,
  fetchUserList,
  resetUserPassword,
  updateUser,
} from "@/domain/user-management/service";
import type {
  ResetPasswordResult,
  ResetPasswordValues,
  UserDetailRecord,
  UserFormValues,
  UserListQuery,
} from "@/domain/user-management/types";
import type { ListRequestParams } from "@/shared/types/list";

export const userManagementQueryKeys = {
  all: ["user-management"] as const,
  list: (params: ListRequestParams<UserListQuery>) =>
    [...userManagementQueryKeys.all, "list", params] as const,
  detail: (userId: string | number) =>
    [...userManagementQueryKeys.all, "detail", userId] as const,
};

type MutationOverride<TData, TVariables> = Omit<
  UseMutationOptions<TData, Error, TVariables, unknown>,
  "mutationFn" | "mutationKey"
>;

export function userDetailQueryOptions(userId: string | number) {
  return queryOptions({
    queryKey: userManagementQueryKeys.detail(userId),
    queryFn: ({ signal }) => fetchUserDetail(userId, signal),
  });
}

export function createUserMutationOptions(
  queryClient: QueryClient,
  overrides?: MutationOverride<UserDetailRecord, UserFormValues>,
) {
  return mutationOptions<UserDetailRecord, Error, UserFormValues>({
    mutationKey: [...userManagementQueryKeys.all, "create"],
    mutationFn: (values) => createUser(values),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({
        queryKey: userManagementQueryKeys.all,
      });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function updateUserMutationOptions(
  queryClient: QueryClient,
  userId: string | number,
  overrides?: MutationOverride<UserDetailRecord, UserFormValues>,
) {
  return mutationOptions<UserDetailRecord, Error, UserFormValues>({
    mutationKey: [...userManagementQueryKeys.all, "update", userId],
    mutationFn: (values) => updateUser(userId, values),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({
        queryKey: userManagementQueryKeys.all,
      });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function enableUserMutationOptions(
  queryClient: QueryClient,
  overrides?: MutationOverride<UserDetailRecord, string | number>,
) {
  return mutationOptions<UserDetailRecord, Error, string | number>({
    mutationKey: [...userManagementQueryKeys.all, "enable"],
    mutationFn: (userId) => enableUser(userId),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({
        queryKey: userManagementQueryKeys.all,
      });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function disableUserMutationOptions(
  queryClient: QueryClient,
  overrides?: MutationOverride<UserDetailRecord, string | number>,
) {
  return mutationOptions<UserDetailRecord, Error, string | number>({
    mutationKey: [...userManagementQueryKeys.all, "disable"],
    mutationFn: (userId) => disableUser(userId),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({
        queryKey: userManagementQueryKeys.all,
      });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function resetUserPasswordMutationOptions(
  queryClient: QueryClient,
  userId: string | number,
  overrides?: MutationOverride<ResetPasswordResult, ResetPasswordValues>,
) {
  return mutationOptions<ResetPasswordResult, Error, ResetPasswordValues>({
    mutationKey: [...userManagementQueryKeys.all, "reset-password", userId],
    mutationFn: (values) => resetUserPassword(userId, values),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({
        queryKey: userManagementQueryKeys.all,
      });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function deleteUserMutationOptions(
  queryClient: QueryClient,
  overrides?: MutationOverride<void, string | number>,
) {
  return mutationOptions<void, Error, string | number>({
    mutationKey: [...userManagementQueryKeys.all, "delete"],
    mutationFn: (userId) => deleteUser(userId),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({
        queryKey: userManagementQueryKeys.all,
      });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export { fetchUserList };
