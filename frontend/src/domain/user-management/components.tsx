import { Tag } from "antd";
import type { FormDialogOption } from "@/shared/ui";
import type { UserRoleRef } from "@/domain/user-management/types";

export const userStatusOptions: FormDialogOption[] = [
  {
    label: "启用",
    value: true,
  },
  {
    label: "禁用",
    value: false,
  },
];

export function UserRoleTags({
  roles,
}: {
  roles: UserRoleRef[];
}): JSX.Element {
  if (roles.length === 0) {
    return <Tag color="default">未分配</Tag>;
  }
  return (
    <>
      {roles.map((role) => (
        <Tag
          key={role.id}
          color={role.code === "admin" ? "blue" : "default"}
        >
          {role.name}
        </Tag>
      ))}
    </>
  );
}

export function UserStatusTag({
  isActive,
}: {
  isActive: boolean;
}): JSX.Element {
  return isActive ? (
    <Tag color="success">启用</Tag>
  ) : (
    <Tag color="default">禁用</Tag>
  );
}
