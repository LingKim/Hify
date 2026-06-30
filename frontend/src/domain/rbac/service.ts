import { rbacApi } from "@/domain/rbac/api";
import type {
  PermissionRecord,
  RoleDetailRecord,
  RoleFormValues,
  RoleListQuery,
  RoleListResult,
  RoleOptionRecord,
  UserRoleAssignmentRecord,
  UserRoleFormValues,
} from "@/domain/rbac/types";
import { request } from "@/shared/api";
import type { QueryParams } from "@/shared/api/types";
import type { ListRequestParams } from "@/shared/types/list";

function buildRolePayload(values: RoleFormValues) {
  return {
    code: values.code.trim(),
    name: values.name.trim(),
    description: values.description?.trim() || null,
    status: values.status,
    permissionIds: values.permissionIds,
  };
}

export async function fetchRoleList(
  params: ListRequestParams<RoleListQuery>,
  signal?: AbortSignal,
): Promise<RoleListResult> {
  return request<RoleListResult>({
    request: rbacApi.listRoles,
    query: params as unknown as QueryParams,
    signal,
  });
}

export async function fetchRoleDetail(
  roleId: string | number,
  signal?: AbortSignal,
): Promise<RoleDetailRecord> {
  return request<RoleDetailRecord>({
    request: rbacApi.getRoleDetail,
    pathParams: { roleId },
    signal,
  });
}

export async function createRole(
  values: RoleFormValues,
  signal?: AbortSignal,
): Promise<RoleDetailRecord> {
  return request<RoleDetailRecord>({
    request: rbacApi.createRole,
    body: buildRolePayload(values),
    signal,
  });
}

export async function updateRole(
  roleId: string | number,
  values: RoleFormValues,
  signal?: AbortSignal,
): Promise<RoleDetailRecord> {
  return request<RoleDetailRecord>({
    request: rbacApi.updateRole,
    pathParams: { roleId },
    body: buildRolePayload(values),
    signal,
  });
}

export async function enableRole(
  roleId: string | number,
  signal?: AbortSignal,
): Promise<RoleDetailRecord> {
  return request<RoleDetailRecord>({
    request: rbacApi.enableRole,
    pathParams: { roleId },
    signal,
  });
}

export async function disableRole(
  roleId: string | number,
  signal?: AbortSignal,
): Promise<RoleDetailRecord> {
  return request<RoleDetailRecord>({
    request: rbacApi.disableRole,
    pathParams: { roleId },
    signal,
  });
}

export async function deleteRole(
  roleId: string | number,
  signal?: AbortSignal,
): Promise<void> {
  return request<void>({
    request: rbacApi.deleteRole,
    pathParams: { roleId },
    signal,
  });
}

export async function fetchPermissions(
  signal?: AbortSignal,
): Promise<PermissionRecord[]> {
  return request<PermissionRecord[]>({
    request: rbacApi.listPermissions,
    signal,
  });
}

export async function replaceRolePermissions(
  roleId: string | number,
  permissionIds: number[],
  signal?: AbortSignal,
): Promise<RoleDetailRecord> {
  return request<RoleDetailRecord>({
    request: rbacApi.replaceRolePermissions,
    pathParams: { roleId },
    body: { permissionIds },
    signal,
  });
}

export async function fetchRoleOptions(
  signal?: AbortSignal,
): Promise<RoleOptionRecord[]> {
  return request<RoleOptionRecord[]>({
    request: rbacApi.listRoleOptions,
    signal,
  });
}

export async function fetchUserRoles(
  userId: string | number,
  signal?: AbortSignal,
): Promise<UserRoleAssignmentRecord> {
  return request<UserRoleAssignmentRecord>({
    request: rbacApi.getUserRoles,
    pathParams: { userId },
    signal,
  });
}

export async function replaceUserRoles(
  userId: string | number,
  values: UserRoleFormValues,
  signal?: AbortSignal,
): Promise<UserRoleAssignmentRecord> {
  return request<UserRoleAssignmentRecord>({
    request: rbacApi.replaceUserRoles,
    pathParams: { userId },
    body: values,
    signal,
  });
}
