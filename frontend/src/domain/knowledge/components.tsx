import {
  CheckCircleOutlined,
  DeleteOutlined,
  FileTextOutlined,
  MoreOutlined,
  ReloadOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import { Button, Empty, Progress, Space, Tag, Tooltip, Typography } from "antd";
import type { ReactNode } from "react";
import type {
  KnowledgeBaseDetail,
  KnowledgeBaseSummary,
  KnowledgeDocumentRecord,
  RetrievalHit,
} from "@/domain/knowledge/types";

const statusLabelMap = {
  draft: "草稿",
  enabled: "已启用",
  archived: "已归档",
} as const;

const documentStatusLabelMap = {
  uploaded: "已上传",
  processing: "处理中",
  completed: "已完成",
  failed: "失败",
  disabled: "已停用",
} as const;

const documentStatusColorMap = {
  uploaded: "processing",
  processing: "warning",
  completed: "success",
  failed: "error",
  disabled: "default",
} as const;

export function KnowledgeBaseCard({
  item,
  active,
  onClick,
}: {
  item: KnowledgeBaseSummary;
  active: boolean;
  onClick: () => void;
}): JSX.Element {
  return (
    <button
      className={`knowledge-kb-card${active ? " knowledge-kb-card-active" : ""}`}
      onClick={onClick}
      type="button"
    >
      <span className="knowledge-kb-card-title">
        <Typography.Text strong>{item.name}</Typography.Text>
        <KnowledgeStatusTag status={item.status} />
      </span>
      <span className="knowledge-kb-card-desc">
        {item.description || "暂无描述"}
      </span>
      <span className="knowledge-kb-card-stats">
        <span>
          <strong>{item.documentCount}</strong>文档
        </span>
        <span>
          <strong>{item.chunkCount}</strong>切片
        </span>
        <span>
          <strong>{formatRelativeTime(item.updatedAt)}</strong>更新
        </span>
      </span>
    </button>
  );
}

export function KnowledgeStatusTag({
  status,
}: {
  status: KnowledgeBaseSummary["status"];
}): JSX.Element {
  const color = status === "enabled" ? "success" : status === "draft" ? "gold" : "default";
  return <Tag color={color}>{statusLabelMap[status]}</Tag>;
}

export function KnowledgeHealthPanel({
  detail,
}: {
  detail: KnowledgeBaseDetail;
}): JSX.Element {
  return (
    <aside className="knowledge-health-panel">
      <div className="knowledge-health-ring">
        <Progress
          type="circle"
          percent={detail.health.score}
          size={72}
          strokeColor="var(--brand)"
        />
        <div>
          <Typography.Text strong>检索健康度</Typography.Text>
          <div className="knowledge-muted">{detail.health.label}</div>
        </div>
      </div>
      <Typography.Text type="secondary">
        {detail.health.suggestion || "当前知识库状态稳定，可用于 Agent 会话。"}
      </Typography.Text>
    </aside>
  );
}

export function KnowledgeDocumentList({
  documents,
  loading,
  onDelete,
  onReprocess,
}: {
  documents: KnowledgeDocumentRecord[];
  loading: boolean;
  onDelete: (documentId: number) => void;
  onReprocess: (documentId: number) => void;
}): JSX.Element {
  if (!loading && documents.length === 0) {
    return (
      <Empty
        className="knowledge-empty"
        description="还没有文档，上传后会自动进入解析和向量化流程"
      />
    );
  }

  return (
    <div className="knowledge-doc-list">
      {documents.map((document) => (
        <DocumentRow
          document={document}
          key={document.id}
          onDelete={onDelete}
          onReprocess={onReprocess}
        />
      ))}
    </div>
  );
}

export function RetrievalHitList({
  hits,
}: {
  hits: RetrievalHit[];
}): JSX.Element {
  if (hits.length === 0) {
    return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无命中片段" />;
  }

  return (
    <div className="knowledge-hit-list">
      {hits.map((hit) => (
        <article className="knowledge-hit" key={hit.chunkId}>
          <div className="knowledge-hit-meta">
            <span>
              {hit.documentName}
              {hit.pageNumber != null ? ` · 第 ${hit.pageNumber} 页` : ""}
            </span>
            <strong>{hit.score.toFixed(2)}</strong>
          </div>
          <p>{hit.content}</p>
        </article>
      ))}
    </div>
  );
}

function DocumentRow({
  document,
  onDelete,
  onReprocess,
}: {
  document: KnowledgeDocumentRecord;
  onDelete: (documentId: number) => void;
  onReprocess: (documentId: number) => void;
}): JSX.Element {
  const progress = getDocumentProgress(document);
  return (
    <div className="knowledge-doc-row">
      <div className="knowledge-file-icon">
        <FileTextOutlined />
      </div>
      <div className="knowledge-doc-main">
        <Typography.Text strong ellipsis>
          {document.filename}
        </Typography.Text>
        <span className="knowledge-muted">
          {document.errorMessage ||
            `${document.chunkCount} 个切片 · ${formatFileSize(document.fileSizeBytes)}`}
        </span>
      </div>
      <Tag color={documentStatusColorMap[document.status]}>
        {documentStatusLabelMap[document.status]}
      </Tag>
      <Progress percent={progress} showInfo={false} size="small" />
      <Space size={2}>
        <Tooltip title="重新处理">
          <Button
            icon={<ReloadOutlined />}
            size="small"
            type="link"
            onClick={() => onReprocess(document.id)}
          />
        </Tooltip>
        <Tooltip title="删除">
          <Button
            icon={<DeleteOutlined />}
            size="small"
            type="link"
            onClick={() => onDelete(document.id)}
          />
        </Tooltip>
        <Tooltip title="更多">
          <Button icon={<MoreOutlined />} size="small" type="link" />
        </Tooltip>
      </Space>
    </div>
  );
}

function getDocumentProgress(document: KnowledgeDocumentRecord): number {
  if (document.status === "completed") {
    return 100;
  }
  if (document.status === "failed") {
    return 24;
  }
  if (document.processStage === "embedding") {
    return 72;
  }
  if (document.processStage === "chunking") {
    return 48;
  }
  if (document.processStage === "extracting") {
    return 28;
  }
  return 12;
}

export function KnowledgeMetricStrip({
  detail,
}: {
  detail: KnowledgeBaseDetail;
}): JSX.Element {
  return (
    <div className="knowledge-metrics">
      <MetricItem
        icon={<WarningOutlined />}
        label="处理中"
        value={detail.processingDocumentCount}
      />
      <MetricItem
        icon={<CheckCircleOutlined />}
        label="已完成文档"
        value={Math.max(
          0,
          detail.documentCount - detail.processingDocumentCount - detail.failedDocumentCount,
        )}
      />
      <MetricItem label="知识切片" value={detail.chunkCount} />
    </div>
  );
}

function MetricItem({
  icon,
  label,
  value,
}: {
  icon?: ReactNode;
  label: string;
  value: number;
}): JSX.Element {
  return (
    <div className="knowledge-metric">
      <span className="knowledge-metric-label">
        {icon}
        {label}
      </span>
      <strong>{value}</strong>
    </div>
  );
}

export function formatRelativeTime(value: string | null): string {
  if (value == null) {
    return "-";
  }
  const deltaMs = Date.now() - new Date(value).getTime();
  const minutes = Math.max(1, Math.floor(deltaMs / 60000));
  if (minutes < 60) {
    return `${minutes}m`;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours}h`;
  }
  return `${Math.floor(hours / 24)}d`;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
