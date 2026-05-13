# 知识库 / RAG 模块方案设计

## 1. 背景

Hify 的核心链路是“创建 Agent → 配置工具/知识 → 对话使用”。当前仓库
已经有 `backend/app/knowledge` 骨架、Embedding 客户端、PGVector 查询 helper，
以及 Agent 侧的 `agent_knowledge_bindings` 预留表，但还没有完整的知识库管理、
文档上传、切片入库、检索测试和会话注入闭环。

本模块目标是让用户把团队文档沉淀为可检索知识，并在 Agent 会话中自动引入
相关片段。

## 2. 一期范围

一期范围：

- 知识库 CRUD。
- 上传 `.txt`、`.md`、`.pdf`、`.docx` 文档。
- 文档文本抽取、切片、Embedding、PGVector 索引。
- 文档处理状态展示和失败原因展示。
- 知识库检索测试。
- Agent 绑定知识库。
- 会话运行时根据 Agent 绑定知识库执行 RAG 检索并注入上下文。
- 前端知识库工作台页面，不采用传统 Table 作为主界面。

一期不做：

- OCR 和图片理解。
- 网页爬虫、Notion、飞书、Google Drive 等外部同步。
- 多租户复杂权限和知识库协作共享。
- 专用向量库接入，如 Milvus、Qdrant。
- 高级 rerank、混合检索和知识图谱。
- 大文件断点续传。

## 3. 推荐方案

采用 PostgreSQL + PGVector 一体化方案。

原因：

- 和当前 FastAPI + SQLAlchemy + Alembic + PostgreSQL 技术栈一致。
- 权限、软删除、事务、迁移和业务数据都在同一个数据库内管理。
- 对 Hify 当前 20-50 人内部部署规模足够。
- 降低本地部署和 Docker Compose 的复杂度。

不采用专用向量库作为一期方案。专用向量库检索能力更强，但会增加部署、备份、
一致性和运维成本，不符合当前 MVP 的需求本质。

## 4. 核心设计原则

### 4.1 Knowledge 负责知识资产，Conversation 负责运行编排

`knowledge` 模块负责：

- 知识库、文档和切片持久化。
- 文档解析、切片和向量化。
- 基于 query 的检索能力。

`conversation` 模块负责：

- 加载 Agent 配置。
- 读取 Agent 绑定的知识库。
- 调用 `knowledge` 服务检索。
- 把命中片段注入 LLM messages。
- 保存会话、消息、run 和必要的 RAG 快照。

这样保持后端分层规则：Conversation 是唯一运行编排层。

### 4.2 文件状态可解释

文档上传后不能只显示“成功/失败”。用户需要知道文件处于哪个阶段：

- 已上传，等待解析。
- 正在抽取文本。
- 正在切片。
- 正在向量化。
- 可检索。
- 失败，并显示可理解的失败原因。

### 4.3 检索测试前置

知识库页面必须提供检索测试。用户在把知识库交给 Agent 前，应该能用真实问题
验证命中片段是否可信。

### 4.4 会话注入有上限

RAG 检索结果需要控制：

- Top K。
- 最低相似度。
- 单片长度。
- 总注入字符数或 token 预算。

避免把过多片段塞进上下文，影响回答质量和成本。

## 5. 当前实现状态

已完成：

- Gate 1 产品方向确认：采用 PostgreSQL + PGVector 一体化方案。
- 前端方向确认：采用知识库工作台原型，不做传统 Table 主页面。
- 原型文件：`docs/design/knowledge/prototype.html`。

待继续：

- Gate 2 数据库设计确认。
- Alembic 迁移。
- Gate 3 API 合约设计。
- 后端 ORM、schema、service、router 实现。
- 文档解析、切片、embedding 和检索闭环。
- 前端知识库工作台实现。
- 会话 RAG 注入。
- 接口测试和 E2E 验证。
