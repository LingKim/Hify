import { userManagementApi } from "@/domain/user-management/api";
import type {
  ResetPasswordResult,
  ResetPasswordValues,
  UserDetailRecord,
  UserFormValues,
  UserListQuery,
  UserListResult,
} from "@/domain/user-management/types";
import { request } from "@/shared/api";
import type { QueryParams } from "@/shared/api/types";
import type { ListRequestParams } from "@/shared/types/list";

function buildCreatePayload(values: UserFormValues) {
  return {
    username: values.username.trim(),
    email: values.email.trim(),
    password: values.password,
    role: values.role,
    isActive: values.isActive,
  };
}

function buildUpdatePayload(values: UserFormValues) {
  return {
    username: values.username.trim(),
    email: values.email.trim(),
    role: values.role,
    isActive: values.isActive,
  };
}

export async function fetchUserList(
  params: ListRequestParams<UserListQuery>,
  signal?: AbortSignal,
): Promise<UserListResult> {
  return request<UserListResult>({
    request: userManagementApi.listUsers,
    query: params as unknown as QueryParams,
    signal,
  });
}

export async function fetchUserDetail(
  userId: string | number,
  signal?: AbortSignal,
): Promise<UserDetailRecord> {
  return request<UserDetailRecord>({
    request: userManagementApi.getUserDetail,
    pathParams: { userId },
    signal,
  });
}

export async function createUser(
  values: UserFormValues,
  signal?: AbortSignal,
): Promise<UserDetailRecord> {
  return request<UserDetailRecord>({
    request: userManagementApi.createUser,
    body: buildCreatePayload(values),
    signal,
  });
}

export async function updateUser(
  userId: string | number,
  values: UserFormValues,
  signal?: AbortSignal,
): Promise<UserDetailRecord> {
  return request<UserDetailRecord>({
    request: userManagementApi.updateUser,
    pathParams: { userId },
    body: buildUpdatePayload(values),
    signal,
  });
}

export async function enableUser(
  userId: string | number,
  signal?: AbortSignal,
): Promise<UserDetailRecord> {
  return request<UserDetailRecord>({
    request: userManagementApi.enableUser,
    pathParams: { userId },
    signal,
  });
}

export async function disableUser(
  userId: string | number,
  signal?: AbortSignal,
): Promise<UserDetailRecord> {
  return request<UserDetailRecord>({
    request: userManagementApi.disableUser,
    pathParams: { userId },
    body: {},
    signal,
  });
}

export async function resetUserPassword(
  userId: string | number,
  values: ResetPasswordValues,
  signal?: AbortSignal,
): Promise<ResetPasswordResult> {
  return request<ResetPasswordResult>({
    request: userManagementApi.resetPassword,
    pathParams: { userId },
    body: values,
    signal,
  });
}

export async function deleteUser(
  userId: string | number,
  signal?: AbortSignal,
): Promise<void> {
  return request<void>({
    request: userManagementApi.deleteUser,
    pathParams: { userId },
    signal,
  });
}
