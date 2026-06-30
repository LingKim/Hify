import {
  DeleteOutlined,
  EditOutlined,
  KeyOutlined,
  PlusOutlined,
  PoweroffOutlined,
} from "@ant-design/icons";
import {
  App,
  Button,
  Modal,
  Select,
  Space,
  Tooltip,
  Typography,
} from "antd";
import { useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { currentUserQueryOptions } from "@/domain/auth/queries";
import { hasAnyPermission } from "@/domain/auth/permissions";
import {
  PermissionCodeTag,
  RoleStatusTag,
  roleStatusOptions,
} from "@/domain/rbac/components";
import {
  deleteRoleMutationOptions,
  disableRoleMutationOptions,
  enableRoleMutationOptions,
  fetchRoleList,
  permissionsQueryOptions,
  rbacQueryKeys,
  replaceRolePermissionsMutationOptions,
} from "@/domain/rbac/queries";
import {
  createRole,
  fetchRoleDetail,
  updateRole,
} from "@/domain/rbac/service";
import type {
  PermissionRecord,
  RoleDetailRecord,
  RoleFormValues,
  RoleListQuery,
  RoleSummaryRecord,
} from "@/domain/rbac/types";
import { getErrorMessage } from "@/shared/api";
import { getAccessToken } from "@/shared/auth/token";
import {
  FormDialog,
  ListTable,
  type FormDialogField,
  type ListFilterField,
  type ListTableColumn,
  type ListTableRef,
} from "@/shared/ui";

const INITIAL_ROLE_VALUES: RoleFormValues = {
  code: "",
  name: "",
  description: "",
  status: "enabled",
  permissionIds: [],
};

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function mapDetailToFormValues(
  detail: RoleDetailRecord,
): Partial<RoleFormValues> {
  return {
    code: detail.code,
    name: detail.name,
    description: detail.description ?? "",
    status: detail.status,
    permissionIds: detail.permissions.map((item) => item.id),
  };
}

function buildPermissionOptions(permissions: PermissionRecord[]) {
  return permissions.map((permission) => ({
    label: `${permission.moduleLabel} / ${permission.name}`,
    value: permission.id,
  }));
}

export function RbacPage(): JSX.Element {
  const { message, modal } = App.useApp();
  const queryClient = useQueryClient();
  const tableRef = useRef<ListTableRef<RoleSummaryRecord>>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogMode, setDialogMode] = useState<"create" | "edit">("create");
  const [editingId, setEditingId] = useState<number | undefined>(undefined);
  const [permissionRole, setPermissionRole] =
    useState<RoleSummaryRecord | null>(null);
  const [permissionIds, setPermissionIds] = useState<number[]>([]);
  const currentUserQuery = useQuery(
    currentUserQueryOptions(getAccessToken() !== null),
  );
  const canManageRbac = hasAnyPermission(currentUserQuery.data, [
    "rbac.manage",
  ]);
  const permissionsQuery = useQuery(permissionsQueryOptions());

  const permissionOptions = useMemo(
    () => buildPermissionOptions(permissionsQuery.data ?? []),
    [permissionsQuery.data],
  );

  const enableMutation = useMutation(
    enableRoleMutationOptions(queryClient, {
      onSuccess: async () => {
        message.success("角色已启用");
        tableRef.current?.reload();
      },
      onError: (error) => {
        message.error(`启用失败：${getErrorMessage(error)}`);
      },
    }),
  );
  const disableMutation = useMutation(
    disableRoleMutationOptions(queryClient, {
      onSuccess: async () => {
        message.success("角色已禁用");
        tableRef.current?.reload();
      },
      onError: (error) => {
        message.error(`禁用失败：${getErrorMessage(error)}`);
      },
    }),
  );
  const deleteMutation = useMutation(
    deleteRoleMutationOptions(queryClient, {
      onSuccess: async () => {
        message.success("角色已删除");
        tableRef.current?.reload();
      },
      onError: (error) => {
        message.error(`删除失败：${getErrorMessage(error)}`);
      },
    }),
  );
  const replacePermissionsMutation = useMutation(
    replaceRolePermissionsMutationOptions(queryClient, permissionRole?.id ?? 0, {
      onSuccess: async () => {
        message.success("角色权限已更新");
        setPermissionRole(null);
        setPermissionIds([]);
        tableRef.current?.reload();
      },
      onError: (error) => {
        message.error(`更新失败：${getErrorMessage(error)}`);
      },
    }),
  );

  const filterSchema = useMemo<ListFilterField[]>(
    () => [
      {
        type: "input",
        key: "keyword",
        label: "关键词",
        placeholder: "搜索角色编码、名称或描述",
      },
      {
        type: "select",
        key: "status",
        label: "状态",
        placeholder: "全部状态",
        options: roleStatusOptions,
      },
    ],
    [],
  );

  const formSchema = useMemo<FormDialogField[]>(
    () => [
      {
        type: "input",
        key: "code",
        label: "角色编码",
        required: true,
        disabled: dialogMode === "edit",
        placeholder: "例如 ops",
      },
      {
        type: "input",
        key: "name",
        label: "角色名称",
        required: true,
        placeholder: "请输入角色名称",
      },
      {
        type: "textarea",
        key: "description",
        label: "描述",
        placeholder: "请输入角色职责说明",
      },
      {
        type: "select",
        key: "status",
        label: "状态",
        required: true,
        options: roleStatusOptions,
      },
      {
        type: "custom",
        key: "permissionIds",
        label: "权限",
        colProps: { xs: 24, md: 24 },
        render: ({ value, onChange }) => (
          <Select
            mode="multiple"
            allowClear
            showSearch
            optionFilterProp="label"
            placeholder="选择权限点"
            loading={permissionsQuery.isLoading}
            options={permissionOptions}
            value={(value as number[] | undefined) ?? []}
            onChange={(nextValue) => onChange(nextValue)}
          />
        ),
      },
    ],
    [dialogMode, permissionOptions, permissionsQuery.isLoading],
  );

  const columns = useMemo<ListTableColumn<RoleSummaryRecord>[]>(
    () => [
      {
        title: "角色",
        key: "role",
        render: (_, record) => (
          <div className="provider-cell">
            <Typography.Text strong>{record.name}</Typography.Text>
            <Typography.Text type="secondary">{record.code}</Typography.Text>
          </div>
        ),
      },
      {
        title: "状态",
        dataIndex: "status",
        key: "status",
        render: (_, record) => <RoleStatusTag status={record.status} />,
      },
      {
        title: "系统角色",
        dataIndex: "isSystem",
        key: "isSystem",
        render: (_, record) =>
          record.isSystem ? <PermissionCodeTag code="system" /> : "-",
      },
      {
        title: "用户数",
        dataIndex: "userCount",
        key: "userCount",
      },
      {
        title: "权限数",
        dataIndex: "permissionCount",
        key: "permissionCount",
      },
      {
        title: "更新时间",
        dataIndex: "updatedAt",
        key: "updatedAt",
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

  const openEditDialog = (record: RoleSummaryRecord) => {
    setDialogMode("edit");
    setEditingId(record.id);
    setDialogOpen(true);
  };

  const openPermissionDialog = async (record: RoleSummaryRecord) => {
    const detail = await queryClient.fetchQuery({
      queryKey: rbacQueryKeys.detail(record.id),
      queryFn: ({ signal }) => fetchRoleDetail(record.id, signal),
    });
    setPermissionRole(record);
    setPermissionIds(detail.permissions.map((item) => item.id));
  };

  const confirmToggleRoleStatus = (record: RoleSummaryRecord) => {
    if (record.status === "enabled") {
      modal.confirm({
        title: "确认禁用角色？",
        content: `禁用后，绑定 ${record.name} 的用户将失去该角色权限。`,
        okText: "禁用",
        cancelText: "取消",
        okButtonProps: { danger: true },
        onOk: () => disableMutation.mutateAsync(record.id),
      });
      return;
    }
    void enableMutation.mutateAsync(record.id);
  };

  const confirmDeleteRole = (record: RoleSummaryRecord) => {
    modal.confirm({
      title: "确认删除角色？",
      content: `删除后 ${record.name} 将从角色列表隐藏，已有绑定会同步失效。`,
      okText: "删除",
      cancelText: "取消",
      okButtonProps: { danger: true },
      onOk: () => deleteMutation.mutateAsync(record.id),
    });
  };

  return (
    <div className="provider-page">
      <ListTable<RoleSummaryRecord, RoleListQuery>
        ref={tableRef}
        rowKey="id"
        columns={columns}
        filterSchema={filterSchema}
        queryKey={rbacQueryKeys.list}
        api={fetchRoleList}
        initialPageSize={10}
        toolbar={
          <div className="provider-toolbar">
            <div>
              <Typography.Title level={2}>权限管理</Typography.Title>
              <Typography.Paragraph type="secondary">
                维护角色、权限点和用户授权关系。
              </Typography.Paragraph>
            </div>
            {canManageRbac ? (
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={openCreateDialog}
              >
                新增角色
              </Button>
            ) : null}
          </div>
        }
        tableActions={(record) =>
          canManageRbac ? (
            <Space size={4}>
              <Tooltip title="编辑">
                <Button
                  type="link"
                  size="small"
                  icon={<EditOutlined />}
                  onClick={() => openEditDialog(record)}
                />
              </Tooltip>
              <Tooltip title="权限">
                <Button
                  type="link"
                  size="small"
                  icon={<KeyOutlined />}
                  onClick={() => {
                    void openPermissionDialog(record);
                  }}
                />
              </Tooltip>
              <Tooltip title={record.status === "enabled" ? "禁用" : "启用"}>
                <Button
                  type="link"
                  size="small"
                  icon={<PoweroffOutlined />}
                  disabled={record.isSystem}
                  onClick={() => confirmToggleRoleStatus(record)}
                />
              </Tooltip>
              <Tooltip title="删除">
                <Button
                  type="link"
                  size="small"
                  icon={<DeleteOutlined />}
                  disabled={record.isSystem}
                  onClick={() => confirmDeleteRole(record)}
                />
              </Tooltip>
            </Space>
          ) : null
        }
      />

      {dialogOpen ? (
        <FormDialog<RoleFormValues, RoleDetailRecord>
          open={dialogOpen}
          mode={dialogMode}
          editId={editingId}
          width={760}
          title={(mode) => (mode === "create" ? "新增角色" : "编辑角色")}
          schema={formSchema}
          initialValues={INITIAL_ROLE_VALUES}
          onOpenChange={setDialogOpen}
          detailQueryKey={(roleId) => rbacQueryKeys.detail(roleId)}
          detailApi={fetchRoleDetail}
          mapDetailToValues={mapDetailToFormValues}
          primaryAction={{
            text: dialogMode === "create" ? "创建角色" : "保存变更",
            successMessage:
              dialogMode === "create" ? "角色已创建" : "角色已更新",
            api: async (values, context, signal) => {
              const payload = values as RoleFormValues;
              if (context.mode === "create") {
                return createRole(payload, signal);
              }
              return updateRole(context.editId as number, payload, signal);
            },
          }}
          onSuccess={async () => {
            await queryClient.invalidateQueries({
              queryKey: rbacQueryKeys.all,
            });
            tableRef.current?.reload();
          }}
        />
      ) : null}

      {permissionRole != null ? (
        <Modal
          open={permissionRole != null}
          title={`角色权限：${permissionRole.name}`}
          width={720}
          okText="保存"
          cancelText="取消"
          confirmLoading={replacePermissionsMutation.isPending}
          onCancel={() => {
            setPermissionRole(null);
            setPermissionIds([]);
          }}
          onOk={() => replacePermissionsMutation.mutateAsync(permissionIds)}
        >
          <Select
            mode="multiple"
            allowClear
            showSearch
            optionFilterProp="label"
            placeholder="选择权限点"
            loading={permissionsQuery.isLoading}
            options={permissionOptions}
            value={permissionIds}
            onChange={setPermissionIds}
            style={{ width: "100%" }}
          />
        </Modal>
      ) : null}
    </div>
  );
}
