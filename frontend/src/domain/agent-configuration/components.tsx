import { Alert, Select, Space, Tag, Typography } from "antd";
import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import type {
  AgentKnowledgeBinding,
  AgentOrchestrationMode,
  AgentStatus,
  AgentSummaryRecord,
  AgentToolBinding,
} from "@/domain/agent-configuration/types";
import { providerManagementQueryKeys } from "@/domain/provider-management/queries";
import {
  fetchProviderDetail,
  fetchProviderList,
} from "@/domain/provider-management/service";
import type {
  ProviderDetailRecord,
  ProviderModelRecord,
  ProviderSummaryRecord,
} from "@/domain/provider-management/types";
import { fetchKnowledgeBaseOptions } from "@/domain/knowledge/service";
import type { KnowledgeBaseOption } from "@/domain/knowledge/types";
import { fetchToolOptions } from "@/domain/tool-integration/service";
import type { ToolOptionRecord } from "@/domain/tool-integration/types";

export const agentStatusOptions: Array<{ label: string; value: AgentStatus }> = [
  { label: "草稿", value: "draft" },
  { label: "启用", value: "active" },
  { label: "停用", value: "disabled" },
  { label: "归档", value: "archived" },
];

export const agentOrchestrationModeOptions: Array<{
  label: string;
  value: AgentOrchestrationMode;
}> = [
  { label: "Agent", value: "agent" },
  { label: "Chatbot", value: "chatbot" },
  { label: "Workflow 草稿", value: "workflow" },
];

const statusToneMap: Record<AgentStatus, string> = {
  draft: "processing",
  active: "success",
  disabled: "default",
  archived: "error",
};

export function AgentStatusTags({
  record,
}: {
  record: AgentSummaryRecord;
}): JSX.Element {
  return (
    <Space size={[6, 6]} wrap>
      <Tag color={statusToneMap[record.status]}>{record.status}</Tag>
      <Tag color="geekblue">{record.orchestrationMode}</Tag>
      {record.tags.map((tag) => (
        <Tag key={tag}>{tag}</Tag>
      ))}
    </Space>
  );
}

export function AgentModelCell({
  record,
}: {
  record: AgentSummaryRecord;
}): JSX.Element {
  if (record.model == null) {
    return <Tag color="warning">未绑定模型</Tag>;
  }

  return (
    <div className="provider-cell">
      <Typography.Text strong>{record.model.displayName}</Typography.Text>
      <Typography.Text type="secondary">
        {record.model.providerName ?? "未知 Provider"} / {record.model.modelName}
      </Typography.Text>
    </div>
  );
}

function buildProviderOption(provider: ProviderSummaryRecord) {
  return {
    value: provider.id,
    label: (
      <div className="provider-cell">
        <Typography.Text strong>{provider.name}</Typography.Text>
        <Typography.Text type="secondary">
          {provider.providerType} / {provider.status}
          {provider.defaultModel != null
            ? ` / 默认模型 ${provider.defaultModel.displayName}`
            : ""}
        </Typography.Text>
      </div>
    ),
  };
}

function buildModelOption(model: ProviderModelRecord) {
  return {
    value: model.id,
    label: (
      <div className="provider-cell">
        <Typography.Text strong>{model.displayName}</Typography.Text>
        <Typography.Text type="secondary">
          {model.modelName} / {model.status}
          {model.isDefault ? " / 默认" : ""}
        </Typography.Text>
      </div>
    ),
  };
}

export function ProviderInstanceSelectField({
  value,
  onChange,
  setFieldValue,
}: {
  value: unknown;
  onChange: (value: unknown) => void;
  setFieldValue: (key: string, value: unknown) => void;
}): JSX.Element {
  const providerListQuery = useQuery({
    queryKey: providerManagementQueryKeys.list({
      page: 1,
      pageSize: 100,
    }),
    queryFn: ({ signal }) =>
      fetchProviderList(
        {
          page: 1,
          pageSize: 100,
        },
        signal,
      ),
  });

  const options = useMemo(
    () => providerListQuery.data?.list.map(buildProviderOption) ?? [],
    [providerListQuery.data],
  );

  return (
    <Select
      allowClear
      showSearch
      optionFilterProp="label"
      loading={providerListQuery.isFetching}
      placeholder="请选择 Provider 实例"
      options={options}
      value={typeof value === "number" ? value : undefined}
      onChange={(nextValue) => {
        onChange(nextValue);
        setFieldValue("providerModelId", undefined);
      }}
    />
  );
}

export function ProviderModelSelectField({
  value,
  onChange,
  providerInstanceId,
}: {
  value: unknown;
  onChange: (value: unknown) => void;
  providerInstanceId: unknown;
}): JSX.Element {
  const selectedProviderId =
    typeof providerInstanceId === "number" ? providerInstanceId : undefined;

  const providerDetailQuery = useQuery<ProviderDetailRecord>({
    queryKey:
      selectedProviderId !== undefined
        ? providerManagementQueryKeys.detail(selectedProviderId)
        : [...providerManagementQueryKeys.all, "detail", "idle"],
    queryFn: ({ signal }) => {
      if (selectedProviderId === undefined) {
        throw new Error("Provider instance is not selected");
      }

      return fetchProviderDetail(selectedProviderId, signal);
    },
    enabled: selectedProviderId !== undefined,
  });

  const options = useMemo(
    () => providerDetailQuery.data?.models.map(buildModelOption) ?? [],
    [providerDetailQuery.data],
  );

  return (
    <Select
      allowClear
      showSearch
      optionFilterProp="label"
      loading={providerDetailQuery.isFetching}
      disabled={selectedProviderId === undefined}
      placeholder={
        selectedProviderId === undefined
          ? "请先选择 Provider 实例"
          : "请选择 Provider Model"
      }
      options={options}
      value={typeof value === "number" ? value : undefined}
      onChange={onChange}
    />
  );
}

export function ToolBindingsField({
  value,
  onChange,
}: {
  value: unknown;
  onChange: (value: AgentToolBinding[]) => void;
}): JSX.Element {
  const bindings = Array.isArray(value) ? (value as AgentToolBinding[]) : [];
  const toolOptionsQuery = useQuery({
    queryKey: ["tools", "options", "agent-binding"],
    queryFn: ({ signal }) => fetchToolOptions({ status: "enabled" }, signal),
  });
  const selectedIds = bindings
    .filter((item) => item.isEnabled)
    .map((item) => item.toolId);
  const options = useMemo(
    () => (toolOptionsQuery.data ?? []).map(buildToolOption),
    [toolOptionsQuery.data],
  );

  return (
    <Space orientation="vertical" size={8} style={{ width: "100%" }}>
      <Select
        allowClear
        mode="multiple"
        optionFilterProp="label"
        loading={toolOptionsQuery.isFetching}
        placeholder="选择要让 Agent 调用的工具"
        options={options}
        value={selectedIds}
        onChange={(nextIds: number[]) => {
          onChange(
            nextIds.map((toolId, index) => {
              const existingBinding = bindings.find(
                (binding) => binding.toolId === toolId,
              );
              return {
                toolId,
                bindingName: existingBinding?.bindingName ?? null,
                isEnabled: true,
                sortOrder: existingBinding?.sortOrder ?? index,
                config: existingBinding?.config ?? null,
                metadata: existingBinding?.metadata ?? null,
              };
            }),
          );
        }}
      />
      {toolOptionsQuery.data?.length === 0 ? (
        <Alert
          showIcon
          type="warning"
          message="暂无可绑定工具"
          description="请先在工具集成页创建并启用工具，通过测试后再绑定到 Agent。"
        />
      ) : null}
      {bindings.length > 0 ? (
        <Space size={[6, 6]} wrap>
          {bindings.map((item) => (
            <Tag key={item.toolId}>工具 ID {item.toolId}</Tag>
          ))}
        </Space>
      ) : null}
    </Space>
  );
}

function buildToolOption(item: ToolOptionRecord) {
  return {
    value: item.id,
    label: item.name,
    title: item.name,
  };
}

export function KnowledgeBindingsField({
  value,
  onChange,
}: {
  value: unknown;
  onChange: (value: AgentKnowledgeBinding[]) => void;
}): JSX.Element {
  const bindings = Array.isArray(value)
    ? (value as AgentKnowledgeBinding[])
    : [];
  const knowledgeBaseOptionsQuery = useQuery({
    queryKey: ["knowledge", "options", "agent-binding"],
    queryFn: ({ signal }) => fetchKnowledgeBaseOptions(signal),
  });
  const selectedIds = bindings
    .filter((item) => item.isEnabled)
    .map((item) => item.knowledgeBaseId);
  const options = useMemo(
    () =>
      (knowledgeBaseOptionsQuery.data ?? []).map((item) =>
        buildKnowledgeBaseOption(item),
      ),
    [knowledgeBaseOptionsQuery.data],
  );

  return (
    <Space orientation="vertical" size={8} style={{ width: "100%" }}>
      <Select
        allowClear
        mode="multiple"
        optionFilterProp="label"
        loading={knowledgeBaseOptionsQuery.isFetching}
        placeholder="选择要让 Agent 检索的知识库"
        options={options}
        value={selectedIds}
        onChange={(nextIds: number[]) => {
          onChange(
            nextIds.map((knowledgeBaseId, index) => {
              const existingBinding = bindings.find(
                (binding) =>
                  binding.knowledgeBaseId === knowledgeBaseId,
              );
              return {
                knowledgeBaseId,
                isEnabled: true,
                sortOrder: existingBinding?.sortOrder ?? index,
                retrievalConfig:
                  existingBinding?.retrievalConfig ?? null,
                metadata: existingBinding?.metadata ?? null,
              };
            }),
          );
        }}
      />
      {knowledgeBaseOptionsQuery.data?.length === 0 ? (
        <Alert
          showIcon
          type="warning"
          message="暂无可绑定知识库"
          description="请先创建并启用知识库，上传文档完成索引后再绑定到 Agent。"
        />
      ) : null}
      {bindings.length > 0 ? (
        <Space size={[6, 6]} wrap>
          {bindings.map((item) => (
            <Tag key={item.knowledgeBaseId}>知识库 ID {item.knowledgeBaseId}</Tag>
          ))}
        </Space>
      ) : null}
    </Space>
  );
}

function buildKnowledgeBaseOption(item: KnowledgeBaseOption) {
  return {
    value: item.id,
    label: item.name,
    title: item.name,
  };
}
