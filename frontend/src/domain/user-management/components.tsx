import { Tag } from "antd";
import type { FormDialogOption } from "@/shared/ui";
import type { UserRole } from "@/domain/user-management/types";

export const userRoleOptions: FormDialogOption[] = [
  {
    label: "管理员",
    value: "admin",
  },
  {
    label: "普通用户",
    value: "member",
  },
];

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

export function UserRoleTag({ role }: { role: UserRole }): JSX.Element {
  const color = role === "admin" ? "blue" : "default";
  const label = role === "admin" ? "管理员" : "普通用户";
  return <Tag color={color}>{label}</Tag>;
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
