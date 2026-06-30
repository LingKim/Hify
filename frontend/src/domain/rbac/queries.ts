import {
  mutationOptions,
  queryOptions,
  type QueryClient,
  type UseMutationOptions,
} from "@tanstack/react-query";
import {
  createRole,
  deleteRole,
  disableRole,
  enableRole,
  fetchPermissions,
  fetchRoleDetail,
  fetchRoleList,
  fetchRoleOptions,
  fetchUserRoles,
  replaceRolePermissions,
  replaceUserRoles,
  updateRole,
} from "@/domain/rbac/service";
import type {
  PermissionRecord,
  RoleDetailRecord,
  RoleFormValues,
  RoleListQuery,
  RoleOptionRecord,
  UserRoleAssignmentRecord,
  UserRoleFormValues,
} from "@/domain/rbac/types";
import type { ListRequestParams } from "@/shared/types/list";

export const rbacQueryKeys = {
  all: ["rbac"] as const,
  list: (params: ListRequestParams<RoleListQuery>) =>
    [...rbacQueryKeys.all, "roles", params] as const,
  detail: (roleId: string | number) =>
    [...rbacQueryKeys.all, "role", roleId] as const,
  permissions: () => [...rbacQueryKeys.all, "permissions"] as const,
  roleOptions: () => [...rbacQueryKeys.all, "role-options"] as const,
  userRoles: (userId: string | number) =>
    [...rbacQueryKeys.all, "user-roles", userId] as const,
};

type MutationOverride<TData, TVariables> = Omit<
  UseMutationOptions<TData, Error, TVariables, unknown>,
  "mutationFn" | "mutationKey"
>;

export function roleDetailQueryOptions(roleId: string | number) {
  return queryOptions({
    queryKey: rbacQueryKeys.detail(roleId),
    queryFn: ({ signal }) => fetchRoleDetail(roleId, signal),
  });
}

export function permissionsQueryOptions() {
  return queryOptions({
    queryKey: rbacQueryKeys.permissions(),
    queryFn: ({ signal }) => fetchPermissions(signal),
    staleTime: 300_000,
  });
}

export function roleOptionsQueryOptions() {
  return queryOptions({
    queryKey: rbacQueryKeys.roleOptions(),
    queryFn: ({ signal }) => fetchRoleOptions(signal),
    staleTime: 60_000,
  });
}

export function userRolesQueryOptions(userId: string | number) {
  return queryOptions({
    queryKey: rbacQueryKeys.userRoles(userId),
    queryFn: ({ signal }) => fetchUserRoles(userId, signal),
  });
}

export function createRoleMutationOptions(
  queryClient: QueryClient,
  overrides?: MutationOverride<RoleDetailRecord, RoleFormValues>,
) {
  return mutationOptions<RoleDetailRecord, Error, RoleFormValues>({
    mutationKey: [...rbacQueryKeys.all, "create-role"],
    mutationFn: (values) => createRole(values),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({ queryKey: rbacQueryKeys.all });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function updateRoleMutationOptions(
  queryClient: QueryClient,
  roleId: string | number,
  overrides?: MutationOverride<RoleDetailRecord, RoleFormValues>,
) {
  return mutationOptions<RoleDetailRecord, Error, RoleFormValues>({
    mutationKey: [...rbacQueryKeys.all, "update-role", roleId],
    mutationFn: (values) => updateRole(roleId, values),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({ queryKey: rbacQueryKeys.all });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function enableRoleMutationOptions(
  queryClient: QueryClient,
  overrides?: MutationOverride<RoleDetailRecord, string | number>,
) {
  return mutationOptions<RoleDetailRecord, Error, string | number>({
    mutationKey: [...rbacQueryKeys.all, "enable-role"],
    mutationFn: (roleId) => enableRole(roleId),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({ queryKey: rbacQueryKeys.all });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function disableRoleMutationOptions(
  queryClient: QueryClient,
  overrides?: MutationOverride<RoleDetailRecord, string | number>,
) {
  return mutationOptions<RoleDetailRecord, Error, string | number>({
    mutationKey: [...rbacQueryKeys.all, "disable-role"],
    mutationFn: (roleId) => disableRole(roleId),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({ queryKey: rbacQueryKeys.all });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function deleteRoleMutationOptions(
  queryClient: QueryClient,
  overrides?: MutationOverride<void, string | number>,
) {
  return mutationOptions<void, Error, string | number>({
    mutationKey: [...rbacQueryKeys.all, "delete-role"],
    mutationFn: (roleId) => deleteRole(roleId),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({ queryKey: rbacQueryKeys.all });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function replaceRolePermissionsMutationOptions(
  queryClient: QueryClient,
  roleId: string | number,
  overrides?: MutationOverride<RoleDetailRecord, number[]>,
) {
  return mutationOptions<RoleDetailRecord, Error, number[]>({
    mutationKey: [...rbacQueryKeys.all, "replace-role-permissions", roleId],
    mutationFn: (permissionIds) =>
      replaceRolePermissions(roleId, permissionIds),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({ queryKey: rbacQueryKeys.all });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export function replaceUserRolesMutationOptions(
  queryClient: QueryClient,
  userId: string | number,
  overrides?: MutationOverride<
    UserRoleAssignmentRecord,
    UserRoleFormValues
  >,
) {
  return mutationOptions<
    UserRoleAssignmentRecord,
    Error,
    UserRoleFormValues
  >({
    mutationKey: [...rbacQueryKeys.all, "replace-user-roles", userId],
    mutationFn: (values) => replaceUserRoles(userId, values),
    ...overrides,
    onSuccess: async (data, variables, onMutateResult, context) => {
      await queryClient.invalidateQueries({ queryKey: rbacQueryKeys.all });
      await overrides?.onSuccess?.(data, variables, onMutateResult, context);
    },
  });
}

export { fetchRoleList };
export type { PermissionRecord, RoleOptionRecord };
