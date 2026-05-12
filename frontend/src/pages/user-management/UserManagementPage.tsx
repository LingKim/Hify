import {
  DeleteOutlined,
  EditOutlined,
  KeyOutlined,
  PlusOutlined,
  PoweroffOutlined,
} from "@ant-design/icons";
import { App, Button, Input, Select, Space, Tooltip, Typography } from "antd";
import { useMemo, useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  UserRoleTag,
  UserStatusTag,
  userRoleOptions,
  userStatusOptions,
} from "@/domain/user-management/components";
import {
  deleteUserMutationOptions,
  disableUserMutationOptions,
  enableUserMutationOptions,
  fetchUserList,
  userManagementQueryKeys,
} from "@/domain/user-management/queries";
import {
  createUser,
  fetchUserDetail,
  resetUserPassword,
  updateUser,
} from "@/domain/user-management/service";
import type {
  ResetPasswordValues,
  UserDetailRecord,
  UserFormValues,
  UserListQuery,
  UserSummaryRecord,
} from "@/domain/user-management/types";
import { getErrorMessage } from "@/shared/api";
import {
  FormDialog,
  ListTable,
  type FormDialogField,
  type ListFilterField,
  type ListTableColumn,
  type ListTableRef,
} from "@/shared/ui";

const INITIAL_FORM_VALUES: UserFormValues = {
  username: "",
  email: "",
  password: "",
  role: "member",
  isActive: true,
};

const INITIAL_RESET_VALUES: ResetPasswordValues = {
  password: "",
};

function formatDateTime(value: string | null): string {
  if (value == null || value === "") {
    return "-";
  }
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function mapDetailToFormValues(
  detail: UserDetailRecord,
): Partial<UserFormValues> {
  return {
    username: detail.username,
    email: detail.email,
    password: "",
    role: detail.role,
    isActive: detail.isActive,
  };
}

export function UserManagementPage(): JSX.Element {
  const { message, modal } = App.useApp();
  const queryClient = useQueryClient();
  const tableRef = useRef<ListTableRef<UserSummaryRecord>>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogMode, setDialogMode] = useState<"create" | "edit">("create");
  const [editingId, setEditingId] = useState<number | undefined>(undefined);
  const [resetPasswordUser, setResetPasswordUser] =
    useState<UserSummaryRecord | null>(null);

  const enableMutation = useMutation(
    enableUserMutationOptions(queryClient, {
      onSuccess: async () => {
        message.success("用户已启用");
        tableRef.current?.reload();
      },
      onError: (error) => {
        message.error(`启用失败：${getErrorMessage(error)}`);
      },
    }),
  );
  const disableMutation = useMutation(
    disableUserMutationOptions(queryClient, {
      onSuccess: async () => {
        message.success("用户已禁用");
        tableRef.current?.reload();
      },
      onError: (error) => {
        message.error(`禁用失败：${getErrorMessage(error)}`);
      },
    }),
  );
  const deleteMutation = useMutation(
    deleteUserMutationOptions(queryClient, {
      onSuccess: async () => {
        message.success("用户已删除");
        tableRef.current?.reload();
      },
      onError: (error) => {
        message.error(`删除失败：${getErrorMessage(error)}`);
      },
    }),
  );
  const filterSchema = useMemo<ListFilterField[]>(
    () => [
      {
        type: "input",
        key: "keyword",
        label: "关键词",
        placeholder: "搜索用户名或邮箱",
      },
      {
        type: "select",
        key: "role",
        label: "角色",
        placeholder: "全部角色",
        options: userRoleOptions.map((item) => ({
          label: item.label,
          value: item.value as string,
        })),
      },
      {
        type: "custom",
        key: "isActive",
        label: "状态",
        placeholder: "全部状态",
        render: ({ value, onChange }) => (
          <Select
            allowClear
            placeholder="全部状态"
            options={userStatusOptions}
            value={value as boolean | undefined}
            onChange={(nextValue) => onChange(nextValue)}
          />
        ),
      },
    ],
    [],
  );

  const formSchema = useMemo<FormDialogField[]>(
    () => [
      {
        type: "input",
        key: "username",
        label: "用户名",
        required: true,
        placeholder: "请输入用户名",
      },
      {
        type: "input",
        key: "email",
        label: "邮箱",
        required: true,
        placeholder: "请输入邮箱",
        rules: [{ type: "email", message: "请输入合法邮箱" }],
      },
      {
        type: "select",
        key: "role",
        label: "角色",
        required: true,
        options: userRoleOptions,
      },
      {
        type: "select",
        key: "isActive",
        label: "状态",
        required: true,
        options: userStatusOptions,
      },
      {
        type: "custom",
        key: "password",
        label: "初始密码",
        required: dialogMode === "create",
        hidden: dialogMode !== "create",
        colProps: { xs: 24, md: 24 },
        render: ({ value, onChange }) => (
          <Input.Password
            allowClear
            autoComplete="new-password"
            placeholder="至少 8 个字符"
            value={(value as string | undefined) ?? ""}
            onChange={(event) => onChange(event.target.value)}
          />
        ),
      },
    ],
    [dialogMode],
  );

  const resetPasswordSchema = useMemo<FormDialogField[]>(
    () => [
      {
        type: "custom",
        key: "password",
        label: "新密码",
        required: true,
        colProps: { xs: 24, md: 24 },
        render: ({ value, onChange }) => (
          <Input.Password
            allowClear
            autoComplete="new-password"
            placeholder="至少 8 个字符"
            value={(value as string | undefined) ?? ""}
            onChange={(event) => onChange(event.target.value)}
          />
        ),
      },
    ],
    [],
  );

  const columns = useMemo<ListTableColumn<UserSummaryRecord>[]>(
    () => [
      {
        title: "用户",
        key: "user",
        render: (_, record) => (
          <div className="provider-cell">
            <Typography.Text strong>{record.username}</Typography.Text>
            <Typography.Text type="secondary">{record.email}</Typography.Text>
          </div>
        ),
      },
      {
        title: "角色",
        dataIndex: "role",
        key: "role",
        render: (_, record) => <UserRoleTag role={record.role} />,
      },
      {
        title: "状态",
        dataIndex: "isActive",
        key: "isActive",
        render: (_, record) => (
          <UserStatusTag isActive={record.isActive} />
        ),
      },
      {
        title: "最后登录",
        dataIndex: "lastLoginAt",
        key: "lastLoginAt",
        render: (value) => formatDateTime(value as string | null),
      },
      {
        title: "创建时间",
        dataIndex: "createdAt",
        key: "createdAt",
        render: (value) => formatDateTime(value as string),
      },
    ],
    [],
  );

  const openCreateDialog = () => {
    setDialogMode("create");
    setEditingId(undefined);
    setDialogOpen(true);
  };

  const openEditDialog = (record: UserSummaryRecord) => {
    setDialogMode("edit");
    setEditingId(record.id);
    setDialogOpen(true);
  };

  const confirmToggleUserStatus = (record: UserSummaryRecord) => {
    if (record.isActive) {
      modal.confirm({
        title: "确认禁用用户？",
        content: `禁用后 ${record.username} 将无法继续访问系统。`,
        okText: "禁用",
        cancelText: "取消",
        okButtonProps: { danger: true },
        onOk: () => disableMutation.mutateAsync(record.id),
      });
      return;
    }
    void enableMutation.mutateAsync(record.id);
  };

  const confirmDeleteUser = (record: UserSummaryRecord) => {
    modal.confirm({
      title: "确认删除用户？",
      content: `删除后 ${record.username} 将从管理列表隐藏，历史数据归属仍会保留。`,
      okText: "删除",
      cancelText: "取消",
      okButtonProps: { danger: true },
      onOk: () => deleteMutation.mutateAsync(record.id),
    });
  };

  return (
    <div className="provider-page">
      <ListTable<UserSummaryRecord, UserListQuery>
        ref={tableRef}
        rowKey="id"
        columns={columns}
        filterSchema={filterSchema}
        queryKey={userManagementQueryKeys.list}
        api={fetchUserList}
        initialPageSize={10}
        toolbar={
          <div className="provider-toolbar">
            <div>
              <Typography.Title level={2}>用户管理</Typography.Title>
              <Typography.Paragraph type="secondary">
                管理 Hify 内部账号、角色和启用状态。
              </Typography.Paragraph>
            </div>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={openCreateDialog}
            >
              新增用户
            </Button>
          </div>
        }
        tableActions={(record) => (
          <Space size={4}>
            <Tooltip title="编辑">
              <Button
                type="link"
                size="small"
                icon={<EditOutlined />}
                onClick={() => openEditDialog(record)}
              />
            </Tooltip>
            <Tooltip title={record.isActive ? "禁用" : "启用"}>
              <Button
                type="link"
                size="small"
                icon={<PoweroffOutlined />}
                onClick={() => confirmToggleUserStatus(record)}
              />
            </Tooltip>
            <Tooltip title="重置密码">
              <Button
                type="link"
                size="small"
                icon={<KeyOutlined />}
                onClick={() => setResetPasswordUser(record)}
              />
            </Tooltip>
            <Tooltip title="删除">
              <Button
                type="link"
                size="small"
                icon={<DeleteOutlined />}
                onClick={() => confirmDeleteUser(record)}
              />
            </Tooltip>
          </Space>
        )}
      />

      {dialogOpen ? (
        <FormDialog<UserFormValues, UserDetailRecord>
          open={dialogOpen}
          mode={dialogMode}
          editId={editingId}
          width={720}
          title={(mode) => (mode === "create" ? "新增用户" : "编辑用户")}
          schema={formSchema}
          initialValues={INITIAL_FORM_VALUES}
          onOpenChange={setDialogOpen}
          detailQueryKey={(userId) => userManagementQueryKeys.detail(userId)}
          detailApi={fetchUserDetail}
          mapDetailToValues={mapDetailToFormValues}
          primaryAction={{
            text: dialogMode === "create" ? "创建用户" : "保存变更",
            successMessage:
              dialogMode === "create" ? "用户已创建" : "用户已更新",
            api: async (values, context, signal) => {
              const payload = values as UserFormValues;
              if (context.mode === "create") {
                return createUser(payload, signal);
              }
              return updateUser(context.editId as number, payload, signal);
            },
          }}
          onSuccess={async () => {
            await queryClient.invalidateQueries({
              queryKey: userManagementQueryKeys.all,
            });
            tableRef.current?.reload();
          }}
        />
      ) : null}

      {resetPasswordUser != null ? (
        <FormDialog<ResetPasswordValues>
          open={resetPasswordUser != null}
          mode="create"
          width={520}
          title={`重置密码：${resetPasswordUser.username}`}
          schema={resetPasswordSchema}
          initialValues={INITIAL_RESET_VALUES}
          onOpenChange={(open) => {
            if (!open) {
              setResetPasswordUser(null);
            }
          }}
          primaryAction={{
            text: "重置密码",
            successMessage: "密码已重置",
            api: async (values, _context, signal) =>
              resetUserPassword(
                resetPasswordUser.id,
                values as ResetPasswordValues,
                signal,
              ),
          }}
          onSuccess={async () => {
            await queryClient.invalidateQueries({
              queryKey: userManagementQueryKeys.all,
            });
            setResetPasswordUser(null);
            tableRef.current?.reload();
          }}
        />
      ) : null}
    </div>
  );
}
