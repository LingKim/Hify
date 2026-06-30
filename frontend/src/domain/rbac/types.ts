import type { PageResult } from "@/shared/types/list";

export interface RoleListQuery {
  keyword?: string;
  status?: string;
  isSystem?: boolean;
}

export interface RoleSummaryRecord {
  id: number;
  code: string;
  name: string;
  description: string | null;
  status: string;
  isSystem: boolean;
  userCount: number;
  permissionCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface PermissionRecord {
  id: number;
  code: string;
  name: string;
  module: string;
  moduleLabel: string;
  action: string;
  actionLabel: string;
  description: string | null;
  isSystem: boolean;
}

export interface RoleDetailRecord extends RoleSummaryRecord {
  permissions: PermissionRecord[];
}

export type RoleListResult = PageResult<RoleSummaryRecord>;

export interface RoleFormValues {
  code: string;
  name: string;
  description?: string;
  status: string;
  permissionIds: number[];
}

export interface RoleOptionRecord {
  value: number;
  label: string;
  code: string;
  isSystem: boolean;
}

export interface UserRoleAssignmentRecord {
  userId: number;
  username: string;
  email: string;
  isActive: boolean;
  roles: Array<{
    id: number;
    code: string;
    name: string;
    status: string;
    isSystem: boolean;
  }>;
  permissions: string[];
}

export interface UserRoleFormValues {
  roleIds: number[];
}
