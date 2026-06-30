import type { CurrentUser } from "@/domain/auth/types";

export function hasAnyPermission(
  user: CurrentUser | undefined,
  permissionCodes: string[],
): boolean {
  if (permissionCodes.length === 0) {
    return true;
  }
  if (user == null) {
    return false;
  }
  const grantedPermissions = new Set(user.permissions);
  return permissionCodes.some((permissionCode) =>
    grantedPermissions.has(permissionCode),
  );
}

export const routePermissionMap: Record<string, string[]> = {
  "/providers": ["provider.read", "provider.manage"],
  "/agents": ["agent.read", "agent.manage"],
  "/tools": ["tool.read", "tool.manage"],
  "/knowledge": ["knowledge.read", "knowledge.manage"],
  "/chat": ["conversation.use"],
  "/conversations": ["conversation.read", "conversation.manage"],
  "/users": ["user.read", "user.manage"],
  "/rbac": ["rbac.read", "rbac.manage"],
};
