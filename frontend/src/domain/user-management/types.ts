import type { PageResult } from "@/shared/types/list";

export type UserRole = "admin" | "member";

export interface UserListQuery {
  keyword?: string;
  role?: UserRole;
  isActive?: boolean;
}

export interface UserSummaryRecord {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  roleLabel: string;
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
  role: UserRole;
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
