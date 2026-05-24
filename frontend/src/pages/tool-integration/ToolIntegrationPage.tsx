import {
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  HistoryOutlined,
  ImportOutlined,
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
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ToolHealthCell,
  ToolMethodTag,
  ToolParametersEditor,
  ToolRequestTemplateHint,
  ToolStatusTag,
  createEmptyToolParameter,
  mapParameterToFormValue,
  toolAuthTypeOptions,
  toolMethodOptions,
  toolStatusOptions,
} from "@/domain/tool-integration/components";
import {
  deleteToolMutationOptions,
  executeToolTestMutationOptions,
  fetchToolList,
  previewOpenApiMutationOptions,
  toolExecutionLogsQueryOptions,
  toolIntegrationQueryKeys,
} from "@/domain/tool-integration/queries";
import {
  createTool,
  fetchToolDetail,
  updateTool,
} from "@/domain/tool-integration/service";
import type {
  OpenApiPreviewPayload,
  OpenApiToolDraft,
  ToolDetailRecord,
  ToolExecutionResult,
  ToolFormValues,
  ToolListQuery,
  ToolSummaryRecord,
} from "@/domain/tool-integration/types";
import { getErrorMessage } from "@/shared/api";
import {
  FormDialog,
  ListTable,
  type FormDialogField,
  type ListTableColumn,
  type ListTableRef,
} from "@/shared/ui";

const INITIAL_FORM_VALUES: ToolFormValues = {
  name: "",
  description: "",
  status: "draft",
  sourceType: "manual",
  httpMethod: "GET",
  url: "",
  timeoutSeconds: 15,
  headersTemplateJson: '{\n  "Accept": "application/json"\n}',
  queryTemplateJson: "{}",
  bodyTemplateJson: "",
  contentType: "application/json",
  authType: "none",
  secretValue: "",
  headerName: "",
  queryName: "",
  parameters: [createEmptyToolParameter()],
  openapiSource: null,
  metadata: null,
};

interface TestDialogState {
  toolId: number;
  detail: ToolDetailRecord;
}

function formatDateTime(value: string | null): string {
  if (value == null) {
    return "-";
  }
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}

function stringifyJson(value: unknown): string {
  if (value == null) {
    return "";
  }
  return JSON.stringify(value, null, 2);
}

function parseJsonObject(value: string): Record<string, unknown> {
  const normalized = value.trim();
  if (normalized === "") {
    return {};
  }
  const parsed = JSON.parse(normalized) as unknown;
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw new Error("请输入 JSON 对象");
  }
  return parsed as Record<string, unknown>;
}

function mapDetailToFormValues(
  detail: ToolDetailRecord,
): Partial<ToolFormValues> {
  return {
    name: detail.name,
    description: detail.description ?? "",
    status: detail.status,
    sourceType: detail.sourceType,
    httpMethod: detail.httpMethod,
    url: detail.url,
    timeoutSeconds: detail.timeoutSeconds,
    headersTemplateJson: stringifyJson(detail.headersTemplate),
    queryTemplateJson: stringifyJson(detail.queryTemplate),
    bodyTemplateJson: stringifyJson(detail.bodyTemplate),
    contentType: detail.contentType,
    authType: detail.auth.authType,
    secretValue: "",
    headerName: detail.auth.headerName ?? "",
    queryName: detail.auth.queryName ?? "",
    parameters: detail.parameters.map(mapParameterToFormValue),
    openapiSource: detail.openapiSource,
    metadata: detail.metadata,
  };
}

function mapDraftToFormValues(draft: OpenApiToolDraft): ToolFormValues {
  return {
    ...INITIAL_FORM_VALUES,
    name: draft.name,
    description: draft.description ?? "",
    status: draft.status,
    sourceType: draft.sourceType,
    httpMethod: draft.httpMethod,
    url: draft.url,
    timeoutSeconds: draft.timeoutSeconds,
    headersTemplateJson: stringifyJson(draft.headersTemplate),
    queryTemplateJson: stringifyJson(draft.queryTemplate),
    bodyTemplateJson: stringifyJson(draft.bodyTemplate),
    contentType: draft.contentType,
    authType: draft.auth.authType,
    headerName: draft.auth.headerName ?? "",
    queryName: draft.auth.queryName ?? "",
    secretValue: "",
    parameters: draft.parameters.map(mapParameterToFormValue),
    openapiSource: draft.openapiSource,
    metadata: draft.metadata,
  };
}

export function ToolIntegrationPage(): JSX.Element {
  const { message, modal } = App.useApp();
  const queryClient = useQueryClient();
  const tableRef = useRef<ListTableRef<ToolSummaryRecord>>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogMode, setDialogMode] = useState<"create" | "edit">("create");
  const [editingId, setEditingId] = useState<number | undefined>(undefined);
  const [initialValues, setInitialValues] =
    useState<ToolFormValues>(INITIAL_FORM_VALUES);
  const [detailPreview, setDetailPreview] = useState<ToolDetailRecord | null>(
    null,
  );
  const [testDialogState, setTestDialogState] =
    useState<TestDialogState | null>(null);
  const [testResult, setTestResult] = useState<ToolExecutionResult | null>(
    null,
  );
  const [logsTool, setLogsTool] = useState<ToolSummaryRecord | null>(null);
  const [importOpen, setImportOpen] = useState(false);
  const [openApiForm] = Form.useForm<{
    documentJson: string;
    path: string;
    method: string;
    serverUrl?: string;
  }>();
  const [testForm] = Form.useForm<Record<string, unknown>>();

  const deleteMutation = useMutation(deleteToolMutationOptions(queryClient));
  const executeMutation = useMutation(
    executeToolTestMutationOptions(queryClient, testDialogState?.toolId ?? ""),
  );
  const logsQuery = useQuery(
    toolExecutionLogsQueryOptions(logsTool?.id ?? "", {
      page: 1,
      pageSize: 20,
      source: "test",
    }),
  );
  const previewOpenApiMutation = useMutation(
    previewOpenApiMutationOptions({
      onSuccess: (result) => {
        setImportOpen(false);
        setDialogMode("create");
        setEditingId(undefined);
        setInitialValues(mapDraftToFormValues(result.draft));
        setDialogOpen(true);
        if (result.warnings.length > 0) {
          void message.warning(result.warnings.join("；"));
        }
      },
      onError: (error) => {
        void message.error(getErrorMessage(error));
      },
    }),
  );

  const columns = useMemo<ListTableColumn<ToolSummaryRecord>[]>(
    () => [
      {
        title: "工具",
        key: "tool",
        render: (_, record) => (
          <div className="tool-cell">
            <Typography.Text strong>{record.name}</Typography.Text>
            <Typography.Text type="secondary" ellipsis>
              {record.url}
            </Typography.Text>
          </div>
        ),
      },
      {
        title: "方法",
        dataIndex: "httpMethod",
        render: (value: string) => <ToolMethodTag method={value} />,
      },
      {
        title: "状态",
        dataIndex: "status",
        render: (value: ToolSummaryRecord["status"]) => (
          <ToolStatusTag status={value} />
        ),
      },
      {
        title: "来源",
        dataIndex: "sourceType",
        render: (value: string) => <Tag>{value}</Tag>,
      },
      {
        title: "鉴权",
        dataIndex: "authType",
        render: (value: string) => <Tag>{value}</Tag>,
      },
      {
        title: "参数",
        dataIndex: "parameterCount",
      },
      {
        title: "绑定",
        dataIndex: "boundAgentCount",
      },
      {
        title: "最近测试",
        key: "lastTest",
        render: (_, record) => <ToolHealthCell record={record} />,
      },
      {
        title: "更新时间",
        dataIndex: "updatedAt",
        render: (value: string) => formatDateTime(value),
      },
    ],
    [],
  );

  const schema = useMemo<FormDialogField[]>(
    () => [
      {
        type: "input",
        key: "name",
        label: "工具名称",
        required: true,
        placeholder: "如 查询订单状态",
      },
      {
        type: "select",
        key: "status",
        label: "状态",
        required: true,
        options: [...toolStatusOptions],
      },
      {
        type: "select",
        key: "sourceType",
        label: "来源",
        required: true,
        options: [
          { label: "手工", value: "manual" },
          { label: "OpenAPI", value: "openapi" },
        ],
      },
      {
        type: "select",
        key: "httpMethod",
        label: "HTTP 方法",
        required: true,
        options: toolMethodOptions,
      },
      {
        type: "custom",
        key: "timeoutSeconds",
        label: "超时秒数",
        render: ({ value, onChange }) => (
          <InputNumber
            min={1}
            max={60}
            value={typeof value === "number" ? value : 15}
            onChange={(nextValue) => onChange(nextValue ?? 15)}
          />
        ),
      },
      {
        type: "input",
        key: "url",
        label: "URL",
        required: true,
        placeholder: "https://api.example.com/orders/{{orderId}}",
        colProps: { xs: 24 },
      },
      {
        type: "textarea",
        key: "description",
        label: "描述",
        rows: 2,
        colProps: { xs: 24 },
      },
      {
        type: "select",
        key: "authType",
        label: "鉴权方式",
        required: true,
        options: [...toolAuthTypeOptions],
      },
      {
        type: "input",
        key: "secretValue",
        label: "密钥",
        placeholder: "编辑时留空表示保留原密钥",
      },
      {
        type: "input",
        key: "headerName",
        label: "Header 名称",
        placeholder: "如 X-API-Key",
      },
      {
        type: "input",
        key: "queryName",
        label: "Query 名称",
        placeholder: "如 api_key",
      },
      {
        type: "input",
        key: "contentType",
        label: "Content-Type",
        placeholder: "application/json",
      },
      {
        type: "custom",
        key: "parameters",
        label: "参数定义",
        colProps: { xs: 24 },
        render: ({ value, onChange }) => (
          <ToolParametersEditor
            value={
              Array.isArray(value)
                ? (value as ToolFormValues["parameters"])
                : []
            }
            onChange={onChange as (nextValue: ToolFormValues["parameters"]) => void}
          />
        ),
      },
      {
        type: "custom",
        key: "headersTemplateJson",
        label: "Headers 模板",
        colProps: { xs: 24 },
        render: ({ value, onChange }) => (
          <div>
            <Input.TextArea
              rows={3}
              value={typeof value === "string" ? value : ""}
              onChange={(event) => onChange(event.target.value)}
            />
            <ToolRequestTemplateHint />
          </div>
        ),
      },
      {
        type: "textarea",
        key: "queryTemplateJson",
        label: "Query 模板",
        rows: 3,
        colProps: { xs: 24 },
      },
      {
        type: "textarea",
        key: "bodyTemplateJson",
        label: "Body 模板",
        rows: 4,
        colProps: { xs: 24 },
      },
    ],
    [],
  );

  const openCreateDialog = () => {
    setDialogMode("create");
    setEditingId(undefined);
    setInitialValues(INITIAL_FORM_VALUES);
    setDialogOpen(true);
  };

  const openEditDialog = (record: ToolSummaryRecord) => {
    setDialogMode("edit");
    setEditingId(record.id);
    setInitialValues(INITIAL_FORM_VALUES);
    setDialogOpen(true);
  };

  const openTestDialog = async (record: ToolSummaryRecord) => {
    try {
      const detail = await fetchToolDetail(record.id);
      setTestResult(null);
      setTestDialogState({ toolId: record.id, detail });
      testForm.resetFields();
      const defaults = Object.fromEntries(
        detail.parameters.map((parameter) => [
          parameter.name,
          parameter.defaultValue ?? "",
        ]),
      );
      testForm.setFieldsValue(defaults);
    } catch (error) {
      void message.error(`工具详情加载失败：${getErrorMessage(error)}`);
    }
  };

  const submitOpenApiPreview = async () => {
    const values = await openApiForm.validateFields();
    let document: Record<string, unknown>;
    try {
      document = parseJsonObject(values.documentJson);
    } catch (error) {
      void message.error(getErrorMessage(error));
      return;
    }
    await previewOpenApiMutation.mutateAsync({
      document,
      operation: {
        path: values.path,
        method: values.method as OpenApiPreviewPayload["operation"]["method"],
      },
      serverUrl: values.serverUrl?.trim() || undefined,
    });
  };

  return (
    <div className="tool-page">
      <Card className="provider-hero-card" variant="borderless">
        <div className="provider-hero">
          <div>
            <Typography.Title level={2}>工具集成</Typography.Title>
            <Typography.Paragraph>
              管理可被 Agent 绑定的 HTTP 工具，先在后台完成配置和测试，再交给编排侧调用。
            </Typography.Paragraph>
          </div>
          <Space>
            <Button
              icon={<ImportOutlined />}
              onClick={() => setImportOpen(true)}
            >
              OpenAPI 导入
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={openCreateDialog}
            >
              新增工具
            </Button>
          </Space>
        </div>
      </Card>

      <ListTable<ToolSummaryRecord, ToolListQuery>
        ref={tableRef}
        rowKey="id"
        filterSchema={[
          {
            type: "input",
            key: "keyword",
            label: "关键词",
            placeholder: "搜索名称、描述或 URL",
          },
          {
            type: "select",
            key: "status",
            label: "状态",
            options: [...toolStatusOptions],
          },
          {
            type: "select",
            key: "httpMethod",
            label: "方法",
            options: toolMethodOptions,
          },
        ]}
        queryKey={(params) => toolIntegrationQueryKeys.list(params)}
        api={fetchToolList}
        columns={columns}
        toolbar={
          <div className="provider-toolbar">
            <Typography.Text type="secondary">
              每个工具保存前端可读配置，密钥只写入后端密文，不在页面回显明文。
            </Typography.Text>
          </div>
        }
        tableActions={(record) => (
          <Space size={4}>
            <Tooltip title="测试执行">
              <Button
                icon={<PlayCircleOutlined />}
                type="link"
                onClick={() => void openTestDialog(record)}
              />
            </Tooltip>
            <Tooltip title="执行日志">
              <Button
                icon={<HistoryOutlined />}
                type="link"
                onClick={() => setLogsTool(record)}
              />
            </Tooltip>
            <Tooltip title="详情">
              <Button
                icon={<EyeOutlined />}
                type="link"
                onClick={async () => {
                  try {
                    setDetailPreview(await fetchToolDetail(record.id));
                  } catch (error) {
                    void message.error(getErrorMessage(error));
                  }
                }}
              />
            </Tooltip>
            <Tooltip title="编辑">
              <Button
                icon={<EditOutlined />}
                type="link"
                onClick={() => openEditDialog(record)}
              />
            </Tooltip>
            <Tooltip title="删除">
              <Button
                icon={<DeleteOutlined />}
                type="link"
                onClick={() => {
                  modal.confirm({
                    title: `确认删除「${record.name}」吗？`,
                    content:
                      record.boundAgentCount > 0
                        ? "该工具已被 Agent 绑定，后端会阻止删除。"
                        : "删除后工具配置会软删除，执行日志保留。",
                    okText: "确认删除",
                    cancelText: "取消",
                    okButtonProps: { danger: true },
                    onOk: async () => {
                      try {
                        await deleteMutation.mutateAsync(record.id);
                        tableRef.current?.reload();
                        void message.success("工具已删除");
                      } catch (error) {
                        void message.error(getErrorMessage(error));
                      }
                    },
                  });
                }}
              />
            </Tooltip>
          </Space>
        )}
      />

      <FormDialog<ToolFormValues, ToolDetailRecord>
        open={dialogOpen}
        mode={dialogMode}
        title={dialogMode === "create" ? "新增工具" : "编辑工具"}
        width={1080}
        onOpenChange={setDialogOpen}
        initialValues={initialValues}
        schema={schema}
        editId={editingId}
        detailQueryKey={(id) => toolIntegrationQueryKeys.detail(id)}
        detailApi={fetchToolDetail}
        mapDetailToValues={mapDetailToFormValues}
        primaryAction={{
          text: dialogMode === "create" ? "创建工具" : "保存工具",
          api: (values, context, signal) => {
            const formValues = {
              ...initialValues,
              ...(values as ToolFormValues),
              openapiSource:
                context.detailData?.openapiSource ?? initialValues.openapiSource,
              metadata: context.detailData?.metadata ?? initialValues.metadata,
            };
            if (context.mode === "edit" && context.editId !== undefined) {
              return updateTool(context.editId, formValues, signal);
            }
            return createTool(formValues, signal);
          },
          successMessage:
            dialogMode === "create" ? "工具已创建" : "工具已更新",
        }}
        onSuccess={async () => {
          await queryClient.invalidateQueries({
            queryKey: toolIntegrationQueryKeys.all,
          });
          tableRef.current?.reload();
        }}
      />

      <Modal
        title="测试执行"
        open={testDialogState !== null}
        onCancel={() => setTestDialogState(null)}
        onOk={async () => {
          if (testDialogState == null) {
            return;
          }
          const values = await testForm.validateFields();
          const result = await executeMutation.mutateAsync({
            parameters: values,
            timeoutSeconds: testDialogState.detail.timeoutSeconds,
          });
          setTestResult(result);
        }}
        confirmLoading={executeMutation.isPending}
        width={860}
        okText="执行测试"
        cancelText="关闭"
      >
        {testDialogState != null ? (
          <div className="tool-test-dialog">
            <Form form={testForm} layout="vertical">
              {testDialogState.detail.parameters.map((parameter) => (
                <Form.Item
                  key={parameter.name}
                  name={parameter.name}
                  label={parameter.label || parameter.name}
                  rules={
                    parameter.isRequired
                      ? [{ required: true, message: `请输入${parameter.label}` }]
                      : undefined
                  }
                >
                  <Input placeholder={parameter.description ?? parameter.name} />
                </Form.Item>
              ))}
              {testDialogState.detail.parameters.length === 0 ? (
                <Typography.Text type="secondary">
                  当前工具没有显式入参，将按现有模板直接执行。
                </Typography.Text>
              ) : null}
            </Form>
            {testResult != null ? (
              <Card size="small" className="tool-test-result">
                <Descriptions size="small" column={1}>
                  <Descriptions.Item label="状态">
                    <Tag color={testResult.status === "success" ? "success" : "error"}>
                      {testResult.status}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="请求 URL">
                    {testResult.request.url}
                  </Descriptions.Item>
                  <Descriptions.Item label="响应状态">
                    {testResult.response.statusCode ?? "-"}
                  </Descriptions.Item>
                  <Descriptions.Item label="响应预览">
                    <pre>{testResult.response.bodyPreview ?? "-"}</pre>
                  </Descriptions.Item>
                </Descriptions>
              </Card>
            ) : null}
          </div>
        ) : null}
      </Modal>

      <Modal
        title={logsTool == null ? "执行日志" : `执行日志：${logsTool.name}`}
        open={logsTool !== null}
        onCancel={() => setLogsTool(null)}
        footer={null}
        width={920}
      >
        <div className="tool-log-list">
          {(logsQuery.data?.list ?? []).map((log) => (
            <article className="tool-log-row" key={log.id}>
              <div>
                <Space>
                  <Tag color={log.status === "success" ? "success" : "error"}>
                    {log.status}
                  </Tag>
                  <ToolMethodTag method={log.requestMethod} />
                  <Typography.Text strong>{log.responseStatusCode ?? "-"}</Typography.Text>
                </Space>
                <Typography.Paragraph ellipsis={{ rows: 2 }}>
                  {log.requestUrl}
                </Typography.Paragraph>
              </div>
              <Typography.Text type="secondary">
                {log.latencyMs}ms · {formatDateTime(log.createdAt)}
              </Typography.Text>
            </article>
          ))}
          {!logsQuery.isLoading && (logsQuery.data?.list ?? []).length === 0 ? (
            <Typography.Text type="secondary">暂无执行日志</Typography.Text>
          ) : null}
        </div>
      </Modal>

      <Modal
        title="OpenAPI 导入预览"
        open={importOpen}
        onCancel={() => setImportOpen(false)}
        onOk={() => void submitOpenApiPreview()}
        confirmLoading={previewOpenApiMutation.isPending}
        okText="生成草稿"
        cancelText="取消"
        width={900}
      >
        <Form
          form={openApiForm}
          layout="vertical"
          initialValues={{
            method: "GET",
            documentJson:
              '{\n  "openapi": "3.0.3",\n  "info": {"title": "Demo API", "version": "1.0.0"},\n  "servers": [{"url": "https://api.example.com"}],\n  "paths": {}\n}',
          }}
        >
          <Form.Item
            name="documentJson"
            label="OpenAPI JSON"
            rules={[{ required: true, message: "请输入 OpenAPI JSON" }]}
          >
            <Input.TextArea rows={10} />
          </Form.Item>
          <Space className="tool-openapi-row" align="start">
            <Form.Item
              name="path"
              label="Operation Path"
              rules={[{ required: true, message: "请输入 path" }]}
            >
              <Input placeholder="/weather" />
            </Form.Item>
            <Form.Item
              name="method"
              label="方法"
              rules={[{ required: true, message: "请选择方法" }]}
            >
              <Select options={toolMethodOptions} />
            </Form.Item>
            <Form.Item name="serverUrl" label="Server URL">
              <Input placeholder="https://api.example.com" />
            </Form.Item>
          </Space>
        </Form>
      </Modal>

      <Modal
        title="工具详情"
        open={detailPreview !== null}
        onCancel={() => setDetailPreview(null)}
        footer={null}
        width={900}
      >
        {detailPreview != null ? (
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="名称">
              {detailPreview.name}
            </Descriptions.Item>
            <Descriptions.Item label="URL">
              {detailPreview.url}
            </Descriptions.Item>
            <Descriptions.Item label="鉴权">
              {detailPreview.auth.authType}
              {detailPreview.auth.secretMasked != null
                ? ` · ${detailPreview.auth.secretMasked}`
                : ""}
            </Descriptions.Item>
            <Descriptions.Item label="参数">
              {detailPreview.parameters.length === 0
                ? "无"
                : detailPreview.parameters.map((item) => item.name).join(", ")}
            </Descriptions.Item>
            <Descriptions.Item label="最近错误">
              {detailPreview.lastErrorMessage ?? "-"}
            </Descriptions.Item>
          </Descriptions>
        ) : null}
      </Modal>
    </div>
  );
}
