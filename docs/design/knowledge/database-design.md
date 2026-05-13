# 知识库 / RAG 数据库设计

## 1. 实体关系概览

```text
users
  └── knowledge_bases
        ├── knowledge_documents
        │     └── knowledge_chunks
        └── knowledge_retrieval_logs

agents
  └── agent_knowledge_bindings
        └── knowledge_bases
```

说明：

- `knowledge_bases` 是知识库主体。
- `knowledge_documents` 保存用户上传的文件和处理状态。
- `knowledge_chunks` 保存可检索文本片段和 PGVector embedding。
- `knowledge_retrieval_logs` 记录检索测试和会话检索摘要，便于排查。
- `agent_knowledge_bindings` 已存在，本模块复用并补充外键约束设计。

## 2. 表设计

### 2.1 knowledge_bases

知识库主体。

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `bigint` | 主键 |
| `owner_user_id` | `bigint` | 创建人，关联 `users.id` |
| `name` | `varchar(128)` | 知识库名称 |
| `description` | `text` | 描述 |
| `status` | `varchar(32)` | `draft`、`enabled`、`archived` |
| `visibility` | `varchar(32)` | `private`、`workspace` |
| `embedding_model` | `varchar(255)` | 当前 embedding 模型 |
| `embedding_dimensions` | `integer` | 向量维度，默认 1024 |
| `chunk_size` | `integer` | 默认切片字符数 |
| `chunk_overlap` | `integer` | 默认切片重叠字符数 |
| `default_top_k` | `integer` | 默认检索 Top K |
| `default_score_threshold` | `numeric(5,4)` | 默认最低相似度 |
| `document_count` | `integer` | 冗余文档数，用于列表 |
| `chunk_count` | `integer` | 冗余切片数，用于列表 |
| `last_indexed_at` | `timestamptz` | 最近完成索引时间 |
| `metadata_json` | `json` | 扩展信息 |
| audit columns | - | `id/created_at/updated_at/deleted_at/version` |

约束：

- `name <> ''`
- `status <> ''`
- `visibility <> ''`
- `embedding_dimensions > 0`
- `chunk_size > 0`
- `chunk_overlap >= 0`
- `chunk_overlap < chunk_size`
- `default_top_k > 0`
- `default_score_threshold >= 0`
- `default_score_threshold <= 1`
- `document_count >= 0`
- `chunk_count >= 0`

索引：

- `ix_knowledge_bases_owner_user_id`
- `ix_knowledge_bases_status`
- `ix_knowledge_bases_deleted_at`
- `ix_knowledge_bases_updated_at`
- `ux_knowledge_bases_owner_user_id_name_active`：
  `(owner_user_id, name)`，仅 `deleted_at IS NULL` 唯一。

### 2.2 knowledge_documents

知识库文档。

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `bigint` | 主键 |
| `knowledge_base_id` | `bigint` | 关联 `knowledge_bases.id` |
| `uploader_user_id` | `bigint` | 上传人，关联 `users.id` |
| `filename` | `varchar(255)` | 原始文件名 |
| `file_ext` | `varchar(16)` | 扩展名 |
| `mime_type` | `varchar(128)` | MIME |
| `file_size_bytes` | `bigint` | 文件大小 |
| `storage_path` | `varchar(1024)` | 本地存储路径或对象存储 key |
| `content_hash` | `varchar(128)` | 内容 hash，用于去重和排查 |
| `status` | `varchar(32)` | 文档处理状态 |
| `process_stage` | `varchar(32)` | 当前处理阶段 |
| `chunk_count` | `integer` | 文档切片数量 |
| `token_count` | `integer` | 粗略 token 数 |
| `error_code` | `varchar(64)` | 失败错误码 |
| `error_message` | `text` | 失败原因 |
| `started_at` | `timestamptz` | 开始处理时间 |
| `completed_at` | `timestamptz` | 完成时间 |
| `metadata_json` | `json` | 页数、解析器版本等 |
| audit columns | - | `id/created_at/updated_at/deleted_at/version` |

状态：

- `uploaded`：已上传，等待处理。
- `processing`：处理中。
- `completed`：已完成，可检索。
- `failed`：处理失败。
- `disabled`：停用，不参与检索。

处理阶段：

- `uploaded`
- `extracting`
- `chunking`
- `embedding`
- `indexed`
- `failed`

约束：

- `filename <> ''`
- `status <> ''`
- `process_stage <> ''`
- `file_size_bytes > 0`
- `chunk_count >= 0`
- `token_count >= 0`

索引：

- `ix_knowledge_documents_knowledge_base_id`
- `ix_knowledge_documents_uploader_user_id`
- `ix_knowledge_documents_status`
- `ix_knowledge_documents_content_hash`
- `ix_knowledge_documents_deleted_at`
- `ix_knowledge_documents_created_at`

### 2.3 knowledge_chunks

可检索文本切片。

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `bigint` | 主键 |
| `knowledge_base_id` | `bigint` | 关联 `knowledge_bases.id` |
| `document_id` | `bigint` | 关联 `knowledge_documents.id` |
| `chunk_index` | `integer` | 文档内切片序号，从 1 开始 |
| `content` | `text` | 切片文本 |
| `content_hash` | `varchar(128)` | 切片内容 hash |
| `token_count` | `integer` | 粗略 token 数 |
| `page_number` | `integer` | 页码，可空 |
| `section_title` | `varchar(255)` | 标题或章节，可空 |
| `source_location_json` | `json` | 段落、页码、坐标等来源信息 |
| `embedding` | `vector(1024)` | PGVector 向量 |
| `embedding_model` | `varchar(255)` | 生成该向量的模型 |
| `metadata_json` | `json` | 扩展信息 |
| audit columns | - | `id/created_at/updated_at/deleted_at/version` |

约束：

- `chunk_index >= 1`
- `content <> ''`
- `token_count >= 0`
- `embedding_model <> ''`

索引：

- `ix_knowledge_chunks_knowledge_base_id`
- `ix_knowledge_chunks_document_id`
- `ix_knowledge_chunks_deleted_at`
- `ux_knowledge_chunks_document_id_chunk_index_active`：
  `(document_id, chunk_index)`，仅 `deleted_at IS NULL` 唯一。
- PGVector 向量索引：
  `ivfflat` 或 `hnsw`，按当前 PostgreSQL/pgvector 版本选择。

一期建议：

- 小数据量可先使用精确 `<=>` 排序检索。
- 迁移中准备向量列和普通索引。
- 当数据量扩大后再补 HNSW/IVFFLAT 参数调优。

### 2.4 knowledge_retrieval_logs

检索日志，用于检索测试和会话 RAG 排查。

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `bigint` | 主键 |
| `knowledge_base_id` | `bigint` | 关联 `knowledge_bases.id` |
| `conversation_id` | `bigint` | 会话 ID，可空 |
| `run_id` | `bigint` | 会话 run ID，可空 |
| `user_id` | `bigint` | 发起人 |
| `source` | `varchar(32)` | `test`、`conversation` |
| `query_text` | `text` | 检索问题 |
| `top_k` | `integer` | 本次 Top K |
| `score_threshold` | `numeric(5,4)` | 本次最低相似度 |
| `hit_count` | `integer` | 命中数量 |
| `latency_ms` | `integer` | 检索耗时 |
| `hits_json` | `json` | 命中片段摘要，不存完整大文本 |
| `metadata_json` | `json` | 扩展信息 |
| audit columns | - | `id/created_at/updated_at/deleted_at/version` |

约束：

- `source <> ''`
- `query_text <> ''`
- `top_k > 0`
- `score_threshold >= 0`
- `score_threshold <= 1`
- `hit_count >= 0`
- `latency_ms >= 0`

索引：

- `ix_knowledge_retrieval_logs_knowledge_base_id`
- `ix_knowledge_retrieval_logs_user_id`
- `ix_knowledge_retrieval_logs_source`
- `ix_knowledge_retrieval_logs_created_at`
- `ix_knowledge_retrieval_logs_conversation_id`
- `ix_knowledge_retrieval_logs_run_id`

## 3. Agent 绑定表补充

当前 `agent_knowledge_bindings.knowledge_base_id` 只有正数校验，没有外键。

本模块建议补充：

- 外键：`agent_knowledge_bindings.knowledge_base_id -> knowledge_bases.id`。
- 保留 `retrieval_config_json`，用于每个 Agent 绑定覆盖知识库默认检索参数。

`retrieval_config_json` 建议结构：

```json
{
  "topK": 5,
  "scoreThreshold": 0.65,
  "maxContextChars": 6000
}
```

## 4. 生命周期规则

知识库：

- `draft`：可上传文档，可测试，不参与会话检索。
- `enabled`：可上传、可测试、可被 Agent 会话检索。
- `archived`：不可新增文档，不参与会话检索，保留历史数据。

文档：

- 上传后创建 `uploaded` 状态。
- 处理开始后改为 `processing`。
- 文本抽取、切片、embedding 全部成功后改为 `completed`。
- 任一阶段失败则改为 `failed`，保留错误信息。
- 删除文档时软删除文档和对应 chunks。

切片：

- 只检索 `deleted_at IS NULL` 且文档 `status = completed` 的切片。
- 文档重新处理时，旧 chunks 软删除，新 chunks 重新写入。

## 5. 迁移策略

迁移分两步：

1. 启用 PGVector 扩展。
2. 创建知识库、文档、切片、检索日志表，并为 Agent 绑定补充外键。

SQLAlchemy/Alembic 注意事项：

- `vector(1024)` 需要通过 `sa.text` 或自定义 SQL 创建，避免引入额外 ORM 类型依赖。
- 如果本地 PostgreSQL 未安装 pgvector，迁移会失败；Docker Compose 需要使用支持
  pgvector 的 PostgreSQL 镜像。
- 当前 embedding 默认维度是 1024，数据库列先按 `vector(1024)` 固化。
- 后续如果更换 embedding 维度，需要新建知识库或做重建索引迁移，不建议原地混用。

## 6. Seed 和回填

一期不需要 seed 数据。

现有 `KnowledgeBase` ORM 是占位类，没有真实字段；迁移落地后需要同步更新 ORM。

已有 `agent_knowledge_bindings` 中如果存在测试数据：

- 若 `knowledge_base_id` 无对应知识库，新增外键前需要先清理或迁移。
- 当前仓库没有发现已提交的知识库真实表迁移，按新表创建处理。

## 7. 待确认问题

- 是否允许普通用户创建 `workspace` 可见知识库，还是只有管理员可创建。
- 上传文件是否先保存到本地磁盘，后续再抽象对象存储。
- `knowledge_retrieval_logs` 是否一期启用，还是只在会话 run 的 metadata 中保存摘要。
