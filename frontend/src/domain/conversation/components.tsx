import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  FileSearchOutlined,
  RobotOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { Empty, Select, Space, Tag, Typography } from "antd";
import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  fetchAgentList,
  agentConfigurationQueryKeys,
} from "@/domain/agent-configuration/queries";
import type { AgentSummaryRecord } from "@/domain/agent-configuration/types";
import type {
  ConversationMessageRecord,
  ConversationRecord,
  ConversationStatus,
} from "@/domain/conversation/types";
import { MarkdownRenderer } from "@/shared/ui";

export const conversationStatusOptions: Array<{
  label: string;
  value: ConversationStatus;
}> = [
  { label: "活跃", value: "active" },
  { label: "归档", value: "archived" },
];

const statusColorMap: Record<ConversationStatus, string> = {
  active: "success",
  archived: "default",
};

const messageStatusIcon = {
  pending: <ClockCircleOutlined />,
  streaming: <ClockCircleOutlined />,
  completed: <CheckCircleOutlined />,
  failed: <CloseCircleOutlined />,
  cancelled: <CloseCircleOutlined />,
};

export function ConversationStatusTag({
  status,
}: {
  status: ConversationStatus;
}): JSX.Element {
  return <Tag color={statusColorMap[status]}>{status}</Tag>;
}

export function ConversationAgentSelect({
  value,
  onChange,
}: {
  value?: number;
  onChange: (agentId: number | undefined) => void;
}): JSX.Element {
  const agentListQuery = useQuery({
    queryKey: agentConfigurationQueryKeys.list({
      page: 1,
      pageSize: 100,
    }),
    queryFn: ({ signal }) =>
      fetchAgentList(
        {
          page: 1,
          pageSize: 100,
        },
        signal,
      ),
  });

  const options = useMemo(
    () =>
      agentListQuery.data?.list.map((agent) => ({
        value: agent.id,
        label: <AgentOption agent={agent} />,
        disabled: agent.status !== "active" || agent.model == null,
      })) ?? [],
    [agentListQuery.data],
  );

  return (
    <Select
      allowClear
      showSearch
      className="conversation-agent-select"
      optionFilterProp="label"
      loading={agentListQuery.isFetching}
      notFoundContent={
        agentListQuery.isFetching ? "正在加载 Agent" : "暂无 Agent，请先创建 Agent"
      }
      placeholder="选择 Agent"
      options={options}
      value={value}
      onChange={onChange}
    />
  );
}

export function ConversationListItem({
  record,
  active,
  onClick,
}: {
  record: ConversationRecord;
  active: boolean;
  onClick: () => void;
}): JSX.Element {
  return (
    <button
      type="button"
      className={`conversation-list-item${active ? " conversation-list-item-active" : ""}`}
      onClick={onClick}
    >
      <span className="conversation-list-item-title">{record.title}</span>
      <span className="conversation-list-item-meta">{record.agentName}</span>
      <span className="conversation-list-item-preview">
        {record.lastMessagePreview ?? "暂无消息"}
      </span>
    </button>
  );
}

export function MessageBubble({
  message,
  retry,
}: {
  message: ConversationMessageRecord;
  retry?: () => void;
}): JSX.Element {
  const isUser = message.role === "user";
  const statusIcon = messageStatusIcon[message.status];

  return (
    <div
      className={`conversation-message-row ${
        isUser ? "conversation-message-row-user" : ""
      }`}
    >
      <div className="conversation-message-avatar">
        {isUser ? <UserOutlined /> : <RobotOutlined />}
      </div>
      <div
        className={`conversation-message-bubble ${
          isUser ? "conversation-message-bubble-user" : ""
        } ${message.status === "failed" ? "conversation-message-bubble-error" : ""}`}
      >
        <div className="conversation-message-content">
          {message.content ? (
            isUser ? (
              message.content
            ) : (
              <MarkdownRenderer content={message.content} />
            )
          ) : message.status === "streaming" ? (
            "正在生成..."
          ) : (
            ""
          )}
        </div>
        {!isUser && message.knowledgeSources.length > 0 ? (
          <KnowledgeSourceStrip sources={message.knowledgeSources} />
        ) : null}
        <div className="conversation-message-meta">
          <Space size={6}>
            {statusIcon}
            <span>{message.status}</span>
            {message.status === "failed" && retry !== undefined ? (
              <Typography.Link onClick={retry}>重试</Typography.Link>
            ) : null}
          </Space>
        </div>
      </div>
    </div>
  );
}

function KnowledgeSourceStrip({
  sources,
}: {
  sources: ConversationMessageRecord["knowledgeSources"];
}): JSX.Element {
  const documentSources = groupKnowledgeSourcesByDocument(sources);

  return (
    <div className="conversation-knowledge-sources">
      <div className="conversation-knowledge-source-title">
        <FileSearchOutlined />
        <span>已引用知识库</span>
      </div>
      <Space size={[6, 6]} wrap>
        {documentSources.map((source) => (
          <Tag key={source.documentId} color="blue">
            {source.documentName}
            {source.pageNumber != null ? ` / 第 ${source.pageNumber} 页` : ""}
            {` · ${(source.maxScore * 100).toFixed(0)}%`}
            {source.hitCount > 1 ? ` · ${source.hitCount} 个片段` : ""}
          </Tag>
        ))}
      </Space>
    </div>
  );
}

function groupKnowledgeSourcesByDocument(
  sources: ConversationMessageRecord["knowledgeSources"],
): Array<{
  documentId: number;
  documentName: string;
  pageNumber: number | null;
  maxScore: number;
  hitCount: number;
}> {
  const sourceMap = new Map<
    number,
    {
      documentId: number;
      documentName: string;
      pageNumber: number | null;
      maxScore: number;
      hitCount: number;
    }
  >();

  sources.forEach((source) => {
    const current = sourceMap.get(source.documentId);
    if (current === undefined) {
      sourceMap.set(source.documentId, {
        documentId: source.documentId,
        documentName: source.documentName,
        pageNumber: source.pageNumber,
        maxScore: source.score,
        hitCount: 1,
      });
      return;
    }

    current.maxScore = Math.max(current.maxScore, source.score);
    current.hitCount += 1;
    if (current.pageNumber == null) {
      current.pageNumber = source.pageNumber;
    }
  });

  return Array.from(sourceMap.values()).sort(
    (first, second) => second.maxScore - first.maxScore,
  );
}

export function EmptyConversation({
  openingMessage,
}: {
  openingMessage?: string | null;
}): JSX.Element {
  return (
    <Empty
      image={Empty.PRESENTED_IMAGE_SIMPLE}
      description={openingMessage ?? "选择 Agent 后发送第一条消息"}
    />
  );
}

function AgentOption({ agent }: { agent: AgentSummaryRecord }): JSX.Element {
  return (
    <div className="provider-cell">
      <Typography.Text strong>{agent.name}</Typography.Text>
      <Typography.Text type="secondary">
        {agent.model?.displayName ?? "未绑定模型"} / {agent.orchestrationMode}
      </Typography.Text>
      {agent.status !== "active" || agent.model == null ? (
        <Typography.Text type="secondary">
          {agent.status !== "active" ? `状态为 ${agent.status}` : "缺少模型"}
        </Typography.Text>
      ) : null}
    </div>
  );
}
