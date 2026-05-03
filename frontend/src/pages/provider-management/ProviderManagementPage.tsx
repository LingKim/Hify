import {
  ApiOutlined,
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  PlayCircleOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import {
  App,
  Button,
  Card,
  Descriptions,
  Form,
  Input,
  InputNumber,
  Modal,
  Select,
  Space,
  Tag,
  Tooltip,
  Typography,
} from "antd";
import { useMemo, useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ProviderModelsEditor,
  ProviderAuthHint,
  ProviderBaseUrlHint,
  ProviderHealthCell,
  ProviderTagSet,
  ProviderTypeField,
  apiFamilyOptions,
  authTypeOptions,
  createEmptyModel,
  providerStatusOptions,
  providerTypeOptions,
} from "@/domain/provider-management/components";
import {
  deleteProviderMutationOptions,
  fetchProviderList,
  providerManagementQueryKeys,
  testProviderConnectionMutationOptions,
} from "@/domain/provider-management/queries";
import {
  createProvider,
  fetchProviderRuntimeConfig,
  fetchProviderDetail,
  invokeProviderTest,
  updateProvider,
} from "@/domain/provider-management/service";
import type {
  ProviderDetailRecord,
  ProviderFormValues,
  ProviderInvokeTestResult,
  ProviderListQuery,
  ProviderRuntimeConfigRecord,
  ProviderSummaryRecord,
} from "@/domain/provider-management/types";
import { getErrorMessage } from "@/shared/api";
import {
  FormDialog,
  ListTable,
  type FormDialogField,
  type ListTableColumn,
  type ListTableRef,
} from "@/shared/ui";

const INITIAL_FORM_VALUES: ProviderFormValues = {
  name: "",
  providerType: "openai",
  apiFamily: "openai_responses",
  baseUrl: "https://api.openai.com/v1",
  status: "active",
  isDefault: false,
  priority: 0,
  notes: "",
  authType: "api_key",
  secretValue: "",
  models: [createEmptyModel(0)],
};

interface InvokeDialogState {
  providerId: number;
  providerName: string;
  models: Array<{
    modelName: string;
    displayName: string;
    isDefault: boolean;
  }>;
}

function mapDetailToFormValues(
  detail: ProviderDetailRecord,
): Partial<ProviderFormValues> {
  return {
    name: detail.name,
    providerType: detail.providerType,
    apiFamily: detail.apiFamily,
    baseUrl: detail.baseUrl,
    status: detail.status,
    isDefault: detail.isDefault,
    priority: detail.priority,
    notes: detail.notes ?? "",
    authType: detail.auth?.authType ?? "api_key",
    secretValue: "",
    models: detail.models.map((model) => ({
      modelName: model.modelName,
      displayName: model.displayName,
      description: model.description ?? "",
      status: model.status,
      isDefault: model.isDefault,
      sortOrder: model.sortOrder,
      supportsChat: model.supportsChat,
      supportsStream: model.supportsStream,
      supportsTools: model.supportsTools,
      supportsStructuredOutput: model.supportsStructuredOutput,
      supportsVisionInput: model.supportsVisionInput,
      supportsAudioInput: model.supportsAudioInput,
      supportsReasoning: model.supportsReasoning,
      supportsEmbeddings: model.supportsEmbeddings,
      contextWindow: model.contextWindow ?? undefined,
      maxOutputTokens: model.maxOutputTokens ?? undefined,
      maxInputTokens: model.maxInputTokens ?? undefined,
      temperatureSupported: model.temperatureSupported,
      topPSupported: model.topPSupported,
    })),
  };
}

export function ProviderManagementPage(): JSX.Element {
  const { message, modal } = App.useApp();
  const queryClient = useQueryClient();
  const tableRef = useRef<ListTableRef<ProviderSummaryRecord>>(null);
  const [invokeForm] = Form.useForm();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogMode, setDialogMode] = useState<"create" | "edit">("create");
  const [editingId, setEditingId] = useState<number | undefined>(undefined);
  const [runtimeConfigPreview, setRuntimeConfigPreview] =
    useState<ProviderRuntimeConfigRecord | null>(null);
  const [invokeDialogState, setInvokeDialogState] =
    useState<InvokeDialogState | null>(null);
  const [invokeResult, setInvokeResult] =
    useState<ProviderInvokeTestResult | null>(null);

  const deleteProviderMutation = useMutation(
    deleteProviderMutationOptions(queryClient),
  );
  const testConnectionMutation = useMutation(
    testProviderConnectionMutationOptions(queryClient),
  );
  const invokeTestMutation = useMutation({
    mutationKey: [...providerManagementQueryKeys.all, "invoke-test-modal"],
    mutationFn: async (values: {
      providerId: number;
      modelName?: string;
      prompt: string;
      temperature?: number;
      maxTokens?: number;
    }) =>
      invokeProviderTest(values.providerId, {
        modelName: values.modelName,
        prompt: values.prompt,
        temperature: values.temperature,
        maxTokens: values.maxTokens,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: providerManagementQueryKeys.all,
      });
    },
  });

  const columns = useMemo<ListTableColumn<ProviderSummaryRecord>[]>(
    () => [
      {
        title: "提供商",
        key: "provider",
        render: (_, record) => (
          <div className="provider-cell">
            <Typography.Text strong>{record.name}</Typography.Text>
            <Typography.Text type="secondary">
              {record.baseUrl}
            </Typography.Text>
          </div>
        ),
      },
      {
        title: "类型与状态",
        key: "tags",
        render: (_, record) => <ProviderTagSet record={record} />,
      },
      {
        title: "健康状态",
        key: "health",
        render: (_, record) => <ProviderHealthCell record={record} />,
      },
      {
        title: "默认模型",
        key: "defaultModel",
        render: (_, record) =>
          record.defaultModel != null ? (
            <div className="provider-cell">
              <Typography.Text strong>
                {record.defaultModel.displayName}
              </Typography.Text>
              <Typography.Text type="secondary">
                {record.defaultModel.modelName}
              </Typography.Text>
            </div>
          ) : (
            <Tag>未设置</Tag>
          ),
      },
      {
        title: "模型数",
        dataIndex: "modelCount",
      },
      {
        title: "密钥状态",
        key: "auth",
        render: (_, record) =>
          record.auth != null ? (
            <div className="provider-cell">
              <Typography.Text>{record.auth.secretMasked}</Typography.Text>
              <Typography.Text type="secondary">
                {record.auth.authType}
              </Typography.Text>
            </div>
          ) : (
            <Tag color="warning">未配置</Tag>
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
        label: "提供商名称",
        required: true,
        placeholder: "如 OpenAI-生产",
      },
      {
        type: "custom",
        key: "providerType",
        label: "提供商类型",
        required: true,
        render: ({ value, onChange, setFieldValue }) => (
          <ProviderTypeField
            value={value}
            onChange={onChange}
            setFieldValue={setFieldValue}
          />
        ),
      },
      {
        type: "select",
        key: "apiFamily",
        label: "协议族",
        required: true,
        options: apiFamilyOptions.map((item) => ({
          label: item.label,
          value: item.value,
        })),
      },
      {
        type: "input",
        key: "baseUrl",
        label: "Base URL",
        required: true,
        placeholder: "如 https://api.openai.com/v1",
        colProps: { xs: 24, md: 24 },
      },
      {
        type: "custom",
        key: "baseUrlHint",
        label: "地址提示",
        colProps: { xs: 24, md: 24 },
        render: ({ formValues }) => (
          <ProviderBaseUrlHint providerType={formValues.providerType} />
        ),
      },
      {
        type: "select",
        key: "status",
        label: "实例状态",
        required: true,
        options: providerStatusOptions.map((item) => ({
          label: item.label,
          value: item.value,
        })),
      },
      {
        type: "custom",
        key: "priority",
        label: "优先级",
        render: ({ value, onChange }) => (
          <InputNumber
            min={0}
            style={{ width: "100%" }}
            value={typeof value === "number" ? value : 0}
            onChange={(nextValue) => onChange(nextValue ?? 0)}
          />
        ),
      },
      {
        type: "switch",
        key: "isDefault",
        label: "设为默认实例",
      },
      {
        type: "select",
        key: "authType",
        label: "鉴权方式",
        required: true,
        options: authTypeOptions.map((item) => ({
          label: item.label,
          value: item.value,
        })),
      },
      {
        type: "custom",
        key: "authHint",
        label: "鉴权提示",
        colProps: { xs: 24, md: 24 },
        render: ({ formValues }) => (
          <ProviderAuthHint
            providerType={formValues.providerType}
            authType={formValues.authType}
          />
        ),
      },
      {
        type: "input",
        key: "secretValue",
        label: "密钥",
        placeholder: "编辑时留空则保持原密钥",
        colProps: { xs: 24, md: 24 },
        hidden: false,
      },
      {
        type: "textarea",
        key: "notes",
        label: "备注",
        rows: 3,
        colProps: { xs: 24, md: 24 },
      },
      {
        type: "custom",
        key: "models",
        label: "模型配置",
        required: true,
        colProps: { xs: 24, md: 24 },
        render: ({ value, onChange }) => (
          <ProviderModelsEditor
            value={value as ProviderFormValues["models"] | undefined}
            onChange={(nextValue) => onChange(nextValue)}
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

  const openEditDialog = (record: ProviderSummaryRecord) => {
    setDialogMode("edit");
    setEditingId(record.id);
    setDialogOpen(true);
  };

  const openInvokeDialog = async (record: ProviderSummaryRecord) => {
    try {
      const detail = await fetchProviderDetail(record.id);
      const models = detail.models.map((model) => ({
        modelName: model.modelName,
        displayName: model.displayName,
        isDefault: model.isDefault,
      }));
      const defaultModel = models.find((model) => model.isDefault) ?? models[0];
      setInvokeResult(null);
      setInvokeDialogState({
        providerId: record.id,
        providerName: record.name,
        models,
      });
      invokeForm.setFieldsValue({
        modelName: defaultModel?.modelName,
        prompt: "请用一句话介绍你自己。",
        temperature: 0.7,
        maxTokens: 512,
      });
    } catch (error) {
      message.error(`加载试跑配置失败：${getErrorMessage(error)}`);
    }
  };

  const closeInvokeDialog = () => {
    if (invokeTestMutation.isPending) {
      return;
    }
    setInvokeDialogState(null);
    setInvokeResult(null);
    invokeForm.resetFields();
  };

  return (
    <div className="provider-page">
      <Card className="provider-hero-card" variant="borderless">
        <div className="provider-hero">
          <div>
            <Typography.Title level={2}>
              模型提供商管理
            </Typography.Title>
            <Typography.Paragraph>
              这是一个面向运营和管理员的统一管理页。单页内维护 Provider
              实例、鉴权方式和模型清单，后端仍保留多模型扩展能力。
            </Typography.Paragraph>
          </div>
          <Space>
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreateDialog}>
              新增提供商
            </Button>
          </Space>
        </div>
      </Card>

      <ListTable<ProviderSummaryRecord, ProviderListQuery>
        ref={tableRef}
        rowKey="id"
        filterSchema={[
          {
            type: "input",
            key: "keyword",
            label: "关键词",
            placeholder: "搜索名称或 Base URL",
          },
          {
            type: "select",
            key: "providerType",
            label: "提供商类型",
            options: providerTypeOptions.map((item) => ({
              label: item.label,
              value: item.value,
            })),
          },
          {
            type: "select",
            key: "status",
            label: "实例状态",
            options: providerStatusOptions.map((item) => ({
              label: item.label,
              value: item.value,
            })),
          },
        ]}
        queryKey={(params) => providerManagementQueryKeys.list(params)}
        api={fetchProviderList}
        columns={columns}
        toolbar={
          <div className="provider-toolbar">
            <Typography.Text type="secondary">
              列表展示的是聚合摘要，编辑时会一次性拉取完整配置。
            </Typography.Text>
          </div>
        }
        tableActions={(record) => (
          <Space size={4}>
            <Tooltip title="测试连接">
              <Button
                type="link"
                icon={<ApiOutlined />}
                loading={
                  testConnectionMutation.isPending &&
                  testConnectionMutation.variables === record.id
                }
                onClick={async () => {
                  try {
                    const result = await testConnectionMutation.mutateAsync(
                      record.id,
                    );
                    if (result.healthState === "healthy") {
                      message.success(
                        `${record.name} 连接成功，耗时 ${result.latencyMs ?? 0}ms`,
                      );
                    } else {
                      message.warning(
                        `${record.name} 已检测：${result.message}`,
                      );
                    }
                    tableRef.current?.reload();
                  } catch (error) {
                    message.error(`连接检测失败：${getErrorMessage(error)}`);
                  }
                }}
              />
            </Tooltip>
            <Tooltip title="运行配置">
              <Button
                type="link"
                icon={<EyeOutlined />}
                onClick={async () => {
                  try {
                    const result = await fetchProviderRuntimeConfig(record.id);
                    setRuntimeConfigPreview(result);
                  } catch (error) {
                    message.error(
                      `运行配置加载失败：${getErrorMessage(error)}`,
                    );
                  }
                }}
              />
            </Tooltip>
            <Tooltip title="试跑模型">
              <Button
                type="link"
                icon={<PlayCircleOutlined />}
                onClick={() => openInvokeDialog(record)}
              />
            </Tooltip>
            <Tooltip title="编辑">
              <Button
                type="link"
                icon={<EditOutlined />}
                onClick={() => openEditDialog(record)}
              />
            </Tooltip>
            <Tooltip title="删除">
              <Button
                type="link"
                danger
                icon={<DeleteOutlined />}
                onClick={() => {
                  modal.confirm({
                    title: `确认删除「${record.name}」吗？`,
                    content: "删除后该提供商实例及其模型配置将被软删除。",
                    okText: "确认删除",
                    cancelText: "取消",
                    okButtonProps: { danger: true },
                    onOk: async () => {
                      await deleteProviderMutation.mutateAsync(record.id);
                      tableRef.current?.reload();
                    },
                  });
                }}
              />
            </Tooltip>
          </Space>
        )}
      />

      {dialogOpen ? (
        <FormDialog<ProviderFormValues, ProviderDetailRecord>
          open={dialogOpen}
          mode={dialogMode}
          editId={editingId}
          width={1120}
          title={(mode) => (mode === "create" ? "新增模型提供商" : "编辑模型提供商")}
          schema={schema}
          initialValues={INITIAL_FORM_VALUES}
          onOpenChange={setDialogOpen}
          detailQueryKey={(providerId) =>
            providerManagementQueryKeys.detail(providerId)
          }
          detailApi={fetchProviderDetail}
          mapDetailToValues={mapDetailToFormValues}
          primaryAction={{
            text: dialogMode === "create" ? "创建提供商" : "保存变更",
            successMessage: dialogMode === "create" ? "提供商已创建" : "提供商已更新",
            api: async (values, context, signal) => {
              const payload = values as ProviderFormValues;
              if (context.mode === "create") {
                return createProvider(payload, signal);
              }
              return updateProvider(context.editId as number, payload, signal);
            },
          }}
          onSuccess={async () => {
            await queryClient.invalidateQueries({
              queryKey: providerManagementQueryKeys.all,
            });
            tableRef.current?.reload();
          }}
        />
      ) : null}

      <Modal
        open={runtimeConfigPreview != null}
        title="运行配置预览"
        width={780}
        onCancel={() => setRuntimeConfigPreview(null)}
        footer={[
          <Button key="close" onClick={() => setRuntimeConfigPreview(null)}>
            关闭
          </Button>,
        ]}
      >
        {runtimeConfigPreview != null ? (
          <Descriptions
            bordered
            column={1}
            size="small"
            items={[
              {
                key: "providerType",
                label: "提供商类型",
                children: runtimeConfigPreview.providerType,
              },
              {
                key: "apiFamily",
                label: "协议族",
                children: runtimeConfigPreview.apiFamily,
              },
              {
                key: "modelName",
                label: "业务模型名",
                children: runtimeConfigPreview.modelName,
              },
              {
                key: "litellmModel",
                label: "LiteLLM 模型串",
                children: runtimeConfigPreview.litellmModel,
              },
              {
                key: "apiBase",
                label: "API Base",
                children: runtimeConfigPreview.apiBase,
              },
              {
                key: "apiKeyMasked",
                label: "密钥",
                children: runtimeConfigPreview.apiKeyMasked,
              },
              {
                key: "extraHeaders",
                label: "额外请求头",
                children:
                  Object.keys(runtimeConfigPreview.extraHeaders).length > 0
                    ? JSON.stringify(
                        runtimeConfigPreview.extraHeaders,
                        null,
                        2,
                      )
                    : "无",
              },
              {
                key: "queryParams",
                label: "额外 Query",
                children:
                  Object.keys(runtimeConfigPreview.queryParams).length > 0
                    ? JSON.stringify(
                        runtimeConfigPreview.queryParams,
                        null,
                        2,
                      )
                    : "无",
              },
            ]}
          />
        ) : null}
      </Modal>

      <Modal
        open={invokeDialogState != null}
        title={
          invokeDialogState != null
            ? `试跑模型 · ${invokeDialogState.providerName}`
            : "试跑模型"
        }
        width={860}
        okText="开始试跑"
        cancelText="关闭"
        confirmLoading={invokeTestMutation.isPending}
        onCancel={closeInvokeDialog}
        onOk={async () => {
          if (invokeDialogState == null) {
            return;
          }
          try {
            const values = await invokeForm.validateFields();
            const result = await invokeTestMutation.mutateAsync({
              providerId: invokeDialogState.providerId,
              modelName: values.modelName,
              prompt: values.prompt,
              temperature:
                typeof values.temperature === "number"
                  ? values.temperature
                  : undefined,
              maxTokens:
                typeof values.maxTokens === "number"
                  ? values.maxTokens
                  : undefined,
            });
            setInvokeResult(result);
            message.success(
              `试跑成功，模型 ${result.modelName} 耗时 ${result.latencyMs}ms`,
            );
            tableRef.current?.reload();
          } catch (error) {
            message.error(`试跑失败：${getErrorMessage(error)}`);
          }
        }}
      >
        {invokeDialogState != null ? (
          <Space direction="vertical" size={16} style={{ width: "100%" }}>
            <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
              这里会用当前 Provider 的真实配置发起一次 LiteLLM 调用，适合验证密钥、模型名和执行链路是否真正可用。
            </Typography.Paragraph>
            <Form form={invokeForm} layout="vertical">
              <Form.Item
                name="modelName"
                label="试跑模型"
                rules={[{ required: true, message: "请选择试跑模型" }]}
              >
                <Select
                  options={invokeDialogState.models.map((model) => ({
                    label: model.isDefault
                      ? `${model.displayName}（默认）`
                      : model.displayName,
                    value: model.modelName,
                  }))}
                />
              </Form.Item>
              <Form.Item
                name="prompt"
                label="测试提示词"
                rules={[{ required: true, message: "请输入测试提示词" }]}
              >
                <Input.TextArea
                  rows={6}
                  placeholder="输入一段简单提示词，验证模型是否能正常返回结果"
                />
              </Form.Item>
              <Space size={16} style={{ width: "100%" }} align="start">
                <Form.Item
                  name="temperature"
                  label="Temperature"
                  style={{ flex: 1, minWidth: 180 }}
                >
                  <InputNumber min={0} max={2} step={0.1} style={{ width: "100%" }} />
                </Form.Item>
                <Form.Item
                  name="maxTokens"
                  label="Max Tokens"
                  style={{ flex: 1, minWidth: 180 }}
                >
                  <InputNumber min={1} max={32768} style={{ width: "100%" }} />
                </Form.Item>
              </Space>
            </Form>
            {invokeResult != null ? (
              <Descriptions
                bordered
                column={1}
                size="small"
                title="试跑结果"
                items={[
                  {
                    key: "modelName",
                    label: "业务模型名",
                    children: invokeResult.modelName,
                  },
                  {
                    key: "litellmModel",
                    label: "LiteLLM 模型串",
                    children: invokeResult.litellmModel,
                  },
                  {
                    key: "latencyMs",
                    label: "耗时",
                    children: `${invokeResult.latencyMs} ms`,
                  },
                  {
                    key: "outputText",
                    label: "返回内容",
                    children: (
                      <Typography.Paragraph
                        style={{ whiteSpace: "pre-wrap", marginBottom: 0 }}
                      >
                        {invokeResult.outputText || "模型已返回，但未提取到文本内容。"}
                      </Typography.Paragraph>
                    ),
                  },
                ]}
              />
            ) : null}
          </Space>
        ) : null}
      </Modal>
    </div>
  );
}
