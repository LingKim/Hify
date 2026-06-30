import type { PageResult } from "@/shared/types/list";

export interface UserRoleRef {
  id: number;
  code: string;
  name: string;
  status: string;
  isSystem: boolean;
}

export interface UserListQuery {
  keyword?: string;
  roleId?: number;
  isActive?: boolean;
}

export interface UserSummaryRecord {
  id: number;
  username: string;
  email: string;
  roles: UserRoleRef[];
  isActive: boolean;
  lastLoginAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export type UserDetailRecord = UserSummaryRecord;

export type UserListResult = PageResult<UserSummaryRecord>;

export interface UserFormValues {
  username: string;
  email: string;
  password?: string;
  isActive: boolean;
}

export interface ResetPasswordValues {
  password: string;
}

export interface ResetPasswordResult {
  id: number;
  passwordUpdated: boolean;
  updatedAt: string;
}
