export const rbacApi = {
  listRoles: "GET /rbac/roles",
  getRoleDetail: "GET /rbac/roles/{roleId}",
  createRole: "POST /rbac/roles",
  updateRole: "PUT /rbac/roles/{roleId}",
  enableRole: "POST /rbac/roles/{roleId}/enable",
  disableRole: "POST /rbac/roles/{roleId}/disable",
  deleteRole: "DELETE /rbac/roles/{roleId}",
  listPermissions: "GET /rbac/permissions",
  replaceRolePermissions: "PUT /rbac/roles/{roleId}/permissions",
  listRoleOptions: "GET /rbac/roles/options",
  getUserRoles: "GET /rbac/users/{userId}/roles",
  replaceUserRoles: "PUT /rbac/users/{userId}/roles",
} as const;
