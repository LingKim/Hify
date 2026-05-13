import {
  CloudUploadOutlined,
  DeleteOutlined,
  PlusOutlined,
  SearchOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import {
  App,
  Button,
  Card,
  Empty,
  Form,
  Input,
  InputNumber,
  Select,
  Space,
  Spin,
  Typography,
} from "antd";
import { useEffect, useMemo, useRef, useState, type RefObject } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  KnowledgeBaseCard,
  KnowledgeDocumentList,
  KnowledgeHealthPanel,
  KnowledgeMetricStrip,
  KnowledgeStatusTag,
  RetrievalHitList,
} from "@/domain/knowledge/components";
import {
  createKnowledgeBaseMutationOptions,
  deleteKnowledgeBaseMutationOptions,
  deleteKnowledgeDocumentMutationOptions,
  knowledgeBaseDetailQueryOptions,
  knowledgeBaseListQueryOptions,
  knowledgeDocumentsQueryOptions,
  reprocessKnowledgeDocumentMutationOptions,
  retrievalTestMutationOptions,
  updateKnowledgeBaseMutationOptions,
  uploadKnowledgeDocumentMutationOptions,
} from "@/domain/knowledge/queries";
import type {
  KnowledgeBaseDetail,
  KnowledgeBaseFormValues,
  KnowledgeDocumentRecord,
  RetrievalTestResult,
} from "@/domain/knowledge/types";
import { getErrorMessage } from "@/shared/api";
import { FormDialog, type FormDialogField } from "@/shared/ui";

const INITIAL_FORM_VALUES: KnowledgeBaseFormValues = {
  name: "",
  description: "",
  status: "draft",
  visibility: "private",
  chunkSize: 800,
  chunkOverlap: 120,
  defaultTopK: 5,
  defaultScoreThreshold: 0.65,
};

export function KnowledgePage(): JSX.Element {
  const { message, modal } = App.useApp();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [keyword, setKeyword] = useState("");
  const [selectedId, setSelectedId] = useState<number | "">("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogMode, setDialogMode] = useState<"create" | "edit">("create");
  const [retrievalForm] = Form.useForm<{ query: string }>();
  const [retrievalResult, setRetrievalResult] =
    useState<RetrievalTestResult | null>(null);

  const listQuery = useQuery(
    knowledgeBaseListQueryOptions({
      page: 1,
      pageSize: 50,
      keyword: keyword || undefined,
    }),
  );
  const knowledgeBases = listQuery.data?.list ?? [];

  useEffect(() => {
    const firstKnowledgeBase = knowledgeBases[0];
    if (selectedId === "" && firstKnowledgeBase !== undefined) {
      setSelectedId(firstKnowledgeBase.id);
    }
  }, [knowledgeBases, selectedId]);

  const detailQuery = useQuery(knowledgeBaseDetailQueryOptions(selectedId));
  const documentsQuery = useQuery(
    knowledgeDocumentsQueryOptions(selectedId, {
      page: 1,
      pageSize: 20,
    }),
  );
  const documents = documentsQuery.data?.list ?? [];
  const detail = detailQuery.data ?? null;

  const createMutation = useMutation(
    createKnowledgeBaseMutationOptions(queryClient, {
      onSuccess: (data) => {
        setDialogOpen(false);
        setSelectedId(data.id);
        void message.success("知识库已创建");
      },
      onError: (error) => {
        void message.error(getErrorMessage(error));
      },
    }),
  );
  const updateMutation = useMutation(
    updateKnowledgeBaseMutationOptions(queryClient, selectedId, {
      onSuccess: () => {
        setDialogOpen(false);
        void message.success("知识库已更新");
      },
      onError: (error) => {
        void message.error(getErrorMessage(error));
      },
    }),
  );
  const deleteKnowledgeBaseMutation = useMutation(
    deleteKnowledgeBaseMutationOptions(queryClient, {
      onSuccess: (_data, deletedId) => {
        const nextKnowledgeBase = knowledgeBases.find(
          (knowledgeBase) => knowledgeBase.id !== deletedId,
        );
        setSelectedId((currentId) =>
          currentId === deletedId ? nextKnowledgeBase?.id ?? "" : currentId,
        );
        setRetrievalResult(null);
        void message.success("知识库已删除");
      },
      onError: (error) => {
        void message.error(getErrorMessage(error));
      },
    }),
  );
  const uploadMutation = useMutation(
    uploadKnowledgeDocumentMutationOptions(queryClient, selectedId, {
      onSuccess: () => {
        void message.success("文档已上传并进入处理流程");
      },
      onError: (error) => {
        void message.error(getErrorMessage(error));
      },
    }),
  );
  const deleteDocumentMutation = useMutation(
    deleteKnowledgeDocumentMutationOptions(queryClient, selectedId, {
      onSuccess: () => {
        void message.success("文档已删除");
      },
      onError: (error) => {
        void message.error(getErrorMessage(error));
      },
    }),
  );
  const reprocessMutation = useMutation(
    reprocessKnowledgeDocumentMutationOptions(queryClient, selectedId, {
      onSuccess: () => {
        void message.success("文档已重新处理");
      },
      onError: (error) => {
        void message.error(getErrorMessage(error));
      },
    }),
  );
  const retrievalMutation = useMutation(
    retrievalTestMutationOptions(selectedId, {
      onSuccess: (data) => {
        setRetrievalResult(data);
      },
      onError: (error) => {
        void message.error(getErrorMessage(error));
      },
    }),
  );

  const fields = useMemo<FormDialogField[]>(
    () => [
      {
        type: "input",
        key: "name",
        label: "知识库名称",
        required: true,
        placeholder: "如 产品资料库",
      },
      {
        type: "textarea",
        key: "description",
        label: "描述",
        placeholder: "说明这个知识库会被哪些 Agent 使用",
      },
      {
        type: "select",
        key: "status",
        label: "状态",
        options: [
          { label: "草稿", value: "draft" },
          { label: "启用", value: "enabled" },
          { label: "归档", value: "archived" },
        ],
      },
      {
        type: "select",
        key: "visibility",
        label: "可见范围",
        options: [
          { label: "仅自己", value: "private" },
          { label: "工作区", value: "workspace" },
        ],
      },
      {
        type: "custom",
        key: "chunkSize",
        label: "切片长度",
        render: ({ value, onChange }) => (
          <InputNumber
            min={100}
            max={4000}
            value={typeof value === "number" ? value : 800}
            onChange={(nextValue) => onChange(nextValue ?? 800)}
          />
        ),
      },
      {
        type: "custom",
        key: "chunkOverlap",
        label: "切片重叠",
        render: ({ value, onChange }) => (
          <InputNumber
            min={0}
            max={1000}
            value={typeof value === "number" ? value : 120}
            onChange={(nextValue) => onChange(nextValue ?? 120)}
          />
        ),
      },
      {
        type: "custom",
        key: "defaultTopK",
        label: "默认 Top K",
        render: ({ value, onChange }) => (
          <InputNumber
            min={1}
            max={20}
            value={typeof value === "number" ? value : 5}
            onChange={(nextValue) => onChange(nextValue ?? 5)}
          />
        ),
      },
      {
        type: "custom",
        key: "defaultScoreThreshold",
        label: "相似度阈值",
        render: ({ value, onChange }) => (
          <InputNumber
            max={1}
            min={0}
            step={0.01}
            value={typeof value === "number" ? value : 0.65}
            onChange={(nextValue) => onChange(nextValue ?? 0.65)}
          />
        ),
      },
    ],
    [],
  );

  return (
    <div className="knowledge-page">
      <header className="knowledge-topbar">
        <div>
          <Typography.Title level={2}>知识库</Typography.Title>
          <Typography.Paragraph type="secondary">
            上传团队文档，Hify 会自动抽取文本、切片、向量化，并在 Agent
            会话时按问题检索相关上下文。
          </Typography.Paragraph>
        </div>
        <Space wrap>
          <Button
            icon={<CloudUploadOutlined />}
            onClick={() => fileInputRef.current?.click()}
          >
            上传文档
          </Button>
          <Button
            icon={<PlusOutlined />}
            type="primary"
            onClick={() => {
              setDialogMode("create");
              setDialogOpen(true);
            }}
          >
            新建知识库
          </Button>
        </Space>
      </header>

      <section className="knowledge-workspace">
        <aside className="knowledge-rail">
          <Input
            allowClear
            prefix={<SearchOutlined />}
            placeholder="搜索知识库、文档、标签"
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
          />
          <div className="knowledge-rail-meta">
            <span>知识空间</span>
            <span>{listQuery.data?.total ?? 0} 个</span>
          </div>
          <div className="knowledge-kb-list">
            {knowledgeBases.map((item) => (
              <KnowledgeBaseCard
                active={item.id === selectedId}
                item={item}
                key={item.id}
                onClick={() => {
                  setSelectedId(item.id);
                  setRetrievalResult(null);
                }}
              />
            ))}
          </div>
          {!listQuery.isLoading && knowledgeBases.length === 0 ? (
            <Empty description="还没有知识库" />
          ) : null}
        </aside>

        <main className="knowledge-detail">
          {detailQuery.isLoading ? <Spin className="knowledge-center" /> : null}
          {!detailQuery.isLoading && detail == null ? (
            <Empty className="knowledge-center" description="请选择知识库" />
          ) : null}
          {detail != null ? (
            <KnowledgeWorkbench
              detail={detail}
              documents={documents}
              documentsLoading={documentsQuery.isLoading}
              fileInputRef={fileInputRef}
              retrievalForm={retrievalForm}
              retrievalLoading={retrievalMutation.isPending}
              retrievalResult={retrievalResult}
              onDeleteDocument={(documentId) => {
                modal.confirm({
                  title: "删除文档",
                  content: "删除后该文档的切片将不再参与检索。",
                  okText: "删除",
                  okButtonProps: { danger: true },
                  onOk: () => deleteDocumentMutation.mutateAsync(documentId),
                });
              }}
              onEdit={() => {
                setDialogMode("edit");
                setDialogOpen(true);
              }}
              onDeleteKnowledgeBase={() => {
                modal.confirm({
                  title: "删除知识库",
                  content:
                    "删除后知识库、文档和切片将不再参与 Agent 会话检索。",
                  okText: "删除",
                  okButtonProps: { danger: true },
                  onOk: () =>
                    deleteKnowledgeBaseMutation.mutateAsync(detail.id),
                });
              }}
              onFileChange={(file) => {
                uploadMutation.mutate(file);
              }}
              onRetrievalTest={(query) => {
                retrievalMutation.mutate({
                  query,
                  topK: detail.defaultTopK,
                  scoreThreshold: detail.defaultScoreThreshold,
                });
              }}
              onReprocessDocument={(documentId) => {
                reprocessMutation.mutate(documentId);
              }}
            />
          ) : null}
        </main>
      </section>

      <FormDialog
        schema={fields}
        initialValues={
          dialogMode === "edit" && detail != null
            ? mapDetailToFormValues(detail)
            : INITIAL_FORM_VALUES
        }
        mode={dialogMode}
        open={dialogOpen}
        title={dialogMode === "create" ? "新建知识库" : "编辑知识库"}
        width={720}
        onOpenChange={setDialogOpen}
        primaryAction={{
          text: dialogMode === "create" ? "创建" : "保存",
          api: async (values) => {
            const formValues = values as KnowledgeBaseFormValues;
            if (dialogMode === "create") {
              return createMutation.mutateAsync(formValues);
            }
            return updateMutation.mutateAsync(formValues);
          },
        }}
      />
    </div>
  );
}

function KnowledgeWorkbench({
  detail,
  documents,
  documentsLoading,
  fileInputRef,
  retrievalForm,
  retrievalLoading,
  retrievalResult,
  onDeleteDocument,
  onDeleteKnowledgeBase,
  onEdit,
  onFileChange,
  onRetrievalTest,
  onReprocessDocument,
}: {
  detail: KnowledgeBaseDetail;
  documents: KnowledgeDocumentRecord[];
  documentsLoading: boolean;
  fileInputRef: RefObject<HTMLInputElement>;
  retrievalForm: ReturnType<typeof Form.useForm<{ query: string }>>[0];
  retrievalLoading: boolean;
  retrievalResult: RetrievalTestResult | null;
  onDeleteDocument: (documentId: number) => void;
  onDeleteKnowledgeBase: () => void;
  onEdit: () => void;
  onFileChange: (file: File) => void;
  onRetrievalTest: (query: string) => void;
  onReprocessDocument: (documentId: number) => void;
}): JSX.Element {
  return (
    <>
      <section className="knowledge-hero">
        <div>
          <div className="knowledge-breadcrumb">知识库 / {detail.name}</div>
          <Space align="center" size={10}>
            <Typography.Title level={3}>{detail.name}</Typography.Title>
            <KnowledgeStatusTag status={detail.status} />
          </Space>
          <Typography.Paragraph type="secondary">
            {detail.description || "暂无描述"}
          </Typography.Paragraph>
          <Space wrap>
            <Button
              icon={<CloudUploadOutlined />}
              type="primary"
              onClick={() => fileInputRef.current?.click()}
            >
              上传文档
            </Button>
            <Button onClick={() => retrievalForm.submit()}>检索测试</Button>
            <Button icon={<SettingOutlined />} onClick={onEdit}>
              知识库设置
            </Button>
            <Button
              danger
              icon={<DeleteOutlined />}
              onClick={onDeleteKnowledgeBase}
            >
              删除知识库
            </Button>
          </Space>
        </div>
        <KnowledgeHealthPanel detail={detail} />
      </section>

      <input
        hidden
        ref={fileInputRef}
        type="file"
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file != null) {
            onFileChange(file);
          }
          event.target.value = "";
        }}
      />

      <section className="knowledge-body-grid">
        <Card
          className="knowledge-section"
          title="文档流"
          extra={<Select defaultValue="all" options={[{ label: "全部状态", value: "all" }]} />}
        >
          <div className="knowledge-drop-zone">
            <strong>拖拽文件到这里，或点击上传</strong>
            <span>支持 PDF、DOCX、TXT、Markdown。单文件建议不超过 20 MB。</span>
          </div>
          <KnowledgeMetricStrip detail={detail} />
          <KnowledgeDocumentList
            documents={documents}
            loading={documentsLoading}
            onDelete={onDeleteDocument}
            onReprocess={onReprocessDocument}
          />
        </Card>

        <div className="knowledge-side-stack">
          <Card className="knowledge-section" title="检索测试">
            <Form
              form={retrievalForm}
              layout="vertical"
              onFinish={(values) => onRetrievalTest(values.query)}
            >
              <Space.Compact className="knowledge-retrieval-input">
                <Form.Item
                  name="query"
                  rules={[{ required: true, message: "请输入检索问题" }]}
                >
                  <Input placeholder="如何配置模型供应商？" />
                </Form.Item>
                <Button htmlType="submit" loading={retrievalLoading} type="primary">
                  测试
                </Button>
              </Space.Compact>
            </Form>
            <RetrievalHitList hits={retrievalResult?.hits ?? []} />
          </Card>

          <Card className="knowledge-section" title="已绑定 Agent">
            {detail.boundAgents.length === 0 ? (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="暂未绑定 Agent"
              />
            ) : (
              <div className="knowledge-agent-list">
                {detail.boundAgents.map((agent) => (
                  <div className="knowledge-agent-item" key={agent.agentId}>
                    <div>
                      <Typography.Text strong>{agent.agentName}</Typography.Text>
                      <span className="knowledge-muted">
                        Top K {agent.topK ?? detail.defaultTopK} · 阈值{" "}
                        {agent.scoreThreshold ?? detail.defaultScoreThreshold}
                      </span>
                    </div>
                    <KnowledgeStatusTag
                      status={agent.isEnabled ? "enabled" : "draft"}
                    />
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </section>
    </>
  );
}

function mapDetailToFormValues(
  detail: KnowledgeBaseDetail,
): KnowledgeBaseFormValues {
  return {
    name: detail.name,
    description: detail.description ?? "",
    status: detail.status,
    visibility: detail.visibility,
    chunkSize: detail.chunkSize,
    chunkOverlap: detail.chunkOverlap,
    defaultTopK: detail.defaultTopK,
    defaultScoreThreshold: detail.defaultScoreThreshold,
  };
}
