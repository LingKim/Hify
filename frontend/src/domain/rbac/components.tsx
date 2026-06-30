import { Tag } from "antd";

export const roleStatusOptions = [
  { label: "启用", value: "enabled" },
  { label: "禁用", value: "disabled" },
];

export function RoleStatusTag({
  status,
}: {
  status: string;
}): JSX.Element {
  return status === "enabled" ? (
    <Tag color="success">启用</Tag>
  ) : (
    <Tag color="default">禁用</Tag>
  );
}

export function PermissionCodeTag({
  code,
}: {
  code: string;
}): JSX.Element {
  return <Tag color="processing">{code}</Tag>;
}
