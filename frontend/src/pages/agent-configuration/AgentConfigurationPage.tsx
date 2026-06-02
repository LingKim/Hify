import {
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import { App, Button, Descriptions, Modal, Space, Tag, Tooltip, Typography } from "antd";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useMemo, useRef, useState } from "react";
import {
  AgentModelCell,
  AgentStatusTags,
  KnowledgeBindingsField,
  ProviderInstanceSelectField,
  ProviderModelSelectField,
  ToolBindingsField,
  agentOrchestrationModeOptions,
  agentStatusOptions,
} from "@/domain/agent-configuration/components";
import {
  deleteAgentMutationOptions,
  fetchAgentConfigPreview,
  fetchAgentList,
  agentConfigurationQueryKeys,
} from "@/domain/agent-configuration/queries";
import {
  createAgent,
  fetchAgentDetail,
  updateAgent,
} from "@/domain/agent-configuration/service";
import type {
  AgentConfigPreviewRecord,
  AgentDetailRecord,
  AgentFormValues,
  AgentListQuery,
  AgentSummaryRecord,
} from "@/domain/agent-configuration/types";
import { getErrorMessage } from "@/shared/api";
import {
  FormDialog,
  ListTable,
  type FormDialogField,
  type ListTableColumn,
  type ListTableRef,
} from "@/shared/ui";

const INITIAL_FORM_VALUES: AgentFormValues = {
  name: "",
  description: "",
  avatarUrl: "",
  status: "draft",
  orchestrationMode: "agent",
  providerInstanceId: undefined,
  providerModelId: undefined,
  systemPrompt: "",
  openingMessage: "",
  modelConfig: {
    temperature: 0.7,
    topP: 1,
    maxTokens: 2048,
  },
  runtimeConfig: {
    stream: true,
    maxIterations: 5,
    memoryWindow: 10,
  },
  workflowRef: null,
  tools: [],
  knowledgeBases: [],
  tags: [],
};

function mapDetailToFormValues(
  detail: AgentDetailRecord,
): Partial<AgentFormValues> {
  return {
    name: detail.name,
    description: detail.description ?? "",
    avatarUrl: detail.avatarUrl ?? "",
    status: detail.status,
    orchestrationMode: detail.orchestrationMode,
    providerInstanceId: detail.providerInstanceId ?? undefined,
    providerModelId: detail.providerModelId ?? undefined,
    systemPrompt: detail.systemPrompt ?? "",
    openingMessage: detail.openingMessage ?? "",
    modelConfig: detail.modelConfig,
    runtimeConfig: detail.runtimeConfig,
    workflowRef: detail.workflowRef,
    tools: detail.tools,
    knowledgeBases: detail.knowledgeBases,
    tags: detail.tags,
  };
}

export function AgentConfigurationPage(): JSX.Element {
  const { message, modal } = App.useApp();
  const queryClient = useQueryClient();
  const tableRef = useRef<ListTableRef<AgentSummaryRecord>>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogMode, setDialogMode] = useState<"create" | "edit">("create");
  const [editingId, setEditingId] = useState<number | undefined>(undefined);
  const [preview, setPreview] = useState<AgentConfigPreviewRecord | null>(null);

  const deleteAgentMutation = useMutation(
    deleteAgentMutationOptions(queryClient),
  );

  const columns = useMemo<ListTableColumn<AgentSummaryRecord>[]>(
    () => [
      {
        title: "Agent",
        key: "agent",
        render: (_, record) => (
          <div className="provider-cell">
            <Typography.Text strong>{record.name}</Typography.Text>
            <Typography.Text type="secondary">
              {record.description ?? "暂无描述"}
            </Typography.Text>
          </div>
        ),
      },
      {
        title: "状态",
        key: "status",
        render: (_, record) => <AgentStatusTags record={record} />,
      },
      {
        title: "默认模型",
        key: "model",
        render: (_, record) => <AgentModelCell record={record} />,
      },
      {
        title: "工具 / 知识库",
        key: "bindings",
        render: (_, record) => (
          <Space size={[6, 6]} wrap>
            <Tag>工具 {record.toolCount}</Tag>
            <Tag>知识库 {record.knowledgeBaseCount}</Tag>
          </Space>
        ),
      },
      {
        title: "最近更新",
        dataIndex: "updatedAt",
        render: (value: string) =>
          new Date(value).toLocaleString("zh-CN", { hour12: false }),
      },
    ],
    [],
  );

  const schema = useMemo<FormDialogField[]>(
    () => [
      {
        type: "input",
        key: "name",
        label: "Agent 名称",
        required: true,
        placeholder: "如 客服助手",
      },
      {
        type: "select",
        key: "status",
        label: "状态",
        required: true,
        options: agentStatusOptions,
      },
      {
        type: "select",
        key: "orchestrationMode",
        label: "编排模式",
        required: true,
        options: agentOrchestrationModeOptions,
      },
      {
        type: "custom",
        key: "providerInstanceId",
        label: "Provider 实例",
        render: ({ value, onChange, setFieldValue }) => (
          <ProviderInstanceSelectField
            value={value}
            onChange={onChange}
            setFieldValue={setFieldValue}
          />
        ),
      },
      {
        type: "custom",
        key: "providerModelId",
        label: "Provider Model",
        render: ({ value, onChange, formValues }) => (
          <ProviderModelSelectField
            value={value}
            onChange={onChange}
            providerInstanceId={formValues.providerInstanceId}
          />
        ),
      },
      {
        type: "textarea",
        key: "description",
        label: "描述",
        rows: 2,
        colProps: { span: 24 },
      },
      {
        type: "textarea",
        key: "systemPrompt",
        label: "系统提示词",
        rows: 5,
        colProps: { span: 24 },
      },
      {
        type: "textarea",
        key: "openingMessage",
        label: "开场白",
        rows: 3,
        colProps: { span: 24 },
      },
      {
        type: "custom",
        key: "tools",
        label: "工具绑定",
        colProps: { span: 24 },
        render: ({ value, onChange }) => (
          <ToolBindingsField
            value={value}
            onChange={(nextBindings) => onChange(nextBindings)}
          />
        ),
      },
      {
        type: "custom",
        key: "knowledgeBases",
        label: "知识库绑定",
        colProps: { span: 24 },
        render: ({ value, onChange }) => (
          <KnowledgeBindingsField
            value={value}
            onChange={(nextBindings) => onChange(nextBindings)}
          />
        ),
      },
    ],
    [],
  );

  const openCreateDialog = () => {
    setDialogMode("create");
    setEditingId(undefined);
    setDialogOpen(true);
  };

  const openEditDialog = (agentId: number) => {
    setDialogMode("edit");
    setEditingId(agentId);
    setDialogOpen(true);
  };

  const handleDelete = (record: AgentSummaryRecord) => {
    modal.confirm({
      title: "删除 Agent",
      content: `确认删除「${record.name}」吗？该操作会软删除配置和绑定关系。`,
      okText: "删除",
      okButtonProps: { danger: true },
      cancelText: "取消",
      onOk: async () => {
        await deleteAgentMutation.mutateAsync(record.id);
        message.success("Agent 已删除");
        tableRef.current?.reload();
      },
    });
  };

  const handlePreview = async (record: AgentSummaryRecord) => {
    try {
      const nextPreview = await fetchAgentConfigPreview(record.id);
      setPreview(nextPreview);
    } catch (error) {
      message.error(getErrorMessage(error));
    }
  };

  return (
    <div className="page-stack">
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>Agent 配置</Typography.Title>
          <Typography.Paragraph type="secondary">
            管理可被对话模块加载的 Agent 配置。Workflow 目前允许保存草稿，
            但暂不启用真实编排。
          </Typography.Paragraph>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreateDialog}>
          新增 Agent
        </Button>
      </div>

      <ListTable<AgentSummaryRecord, AgentListQuery>
        ref={tableRef}
        rowKey="id"
        columns={columns}
        queryKey={agentConfigurationQueryKeys.list}
        api={fetchAgentList}
        initialPageSize={10}
        filterSchema={[
          {
            type: "input",
            key: "keyword",
            label: "关键词",
            placeholder: "搜索 Agent 名称或描述",
          },
          {
            type: "select",
            key: "status",
            label: "状态",
            options: agentStatusOptions,
          },
          {
            type: "select",
            key: "orchestrationMode",
            label: "编排模式",
            options: agentOrchestrationModeOptions,
          },
        ]}
        toolbar={
          <Typography.Text type="secondary">
            Agent 只保存配置；真实运行由 conversation 模块编排。
          </Typography.Text>
        }
        tableActions={(record) => (
          <>
            <Tooltip title="配置预览">
              <Button
                type="link"
                aria-label="配置预览"
                icon={<EyeOutlined />}
                onClick={() => void handlePreview(record)}
              />
            </Tooltip>
            <Tooltip title="编辑">
              <Button
                type="link"
                aria-label="编辑"
                icon={<EditOutlined />}
                onClick={() => openEditDialog(record.id)}
              />
            </Tooltip>
            <Tooltip title="删除">
              <Button
                type="link"
                aria-label="删除"
                icon={<DeleteOutlined />}
                onClick={() => handleDelete(record)}
              />
            </Tooltip>
          </>
        )}
      />

      <FormDialog<AgentFormValues, AgentDetailRecord>
        open={dialogOpen}
        mode={dialogMode}
        title={dialogMode === "create" ? "新增 Agent" : "编辑 Agent"}
        width={860}
        onOpenChange={setDialogOpen}
        editId={editingId}
        initialValues={INITIAL_FORM_VALUES}
        schema={schema}
        detailQueryKey={agentConfigurationQueryKeys.detail}
        detailApi={fetchAgentDetail}
        mapDetailToValues={mapDetailToFormValues}
        primaryAction={{
          text: dialogMode === "create" ? "创建" : "保存",
          successMessage: dialogMode === "create" ? "Agent 已创建" : "Agent 已保存",
          api: async (values, context, signal) =>
            context.mode === "create"
              ? createAgent(values as AgentFormValues, signal)
              : updateAgent(
                  context.editId as string | number,
                  values as AgentFormValues,
                  signal,
                ),
        }}
        onSuccess={async () => {
          await queryClient.invalidateQueries({
            queryKey: agentConfigurationQueryKeys.all,
          });
          tableRef.current?.reload();
        }}
      />

      <Modal
        open={preview !== null}
        title="Agent 配置预览"
        footer={null}
        onCancel={() => setPreview(null)}
      >
        {preview !== null ? (
          <Descriptions column={1} size="small" bordered>
            <Descriptions.Item label="Agent">{preview.name}</Descriptions.Item>
            <Descriptions.Item label="状态">{preview.status}</Descriptions.Item>
            <Descriptions.Item label="编排模式">
              {preview.orchestrationMode}
            </Descriptions.Item>
            <Descriptions.Item label="是否可运行">
              {preview.isRunnable ? "是" : "否"}
            </Descriptions.Item>
            <Descriptions.Item label="模型">
              {preview.model?.displayName ?? "未绑定"}
            </Descriptions.Item>
            <Descriptions.Item label="启用工具">
              {preview.enabledToolIds.join(", ") || "无"}
            </Descriptions.Item>
            <Descriptions.Item label="启用知识库">
              {preview.enabledKnowledgeBaseIds.join(", ") || "无"}
            </Descriptions.Item>
            <Descriptions.Item label="提示">
              {preview.warnings.length > 0
                ? preview.warnings.join("；")
                : "无"}
            </Descriptions.Item>
          </Descriptions>
        ) : null}
      </Modal>
    </div>
  );
}
