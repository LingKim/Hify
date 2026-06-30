# Agent 配置模块方案设计

## 1. 背景

Hify 的核心路径是“创建 Agent → 配置工具/知识 → 对话使用”。

Agent 配置模块负责沉淀可被 `conversation` 加载的 Agent 配置，包括基础信息、默认模型、提示词、工具绑定、知识库绑定和运行参数。

当前模块不是 Workflow 编排引擎，也不承载真实运行逻辑。真实对话执行、SSE、工具调用、知识库检索和未来 Workflow 运行都应继续放在 `conversation` 编排层。

## 2. 一期范围

一期范围：

- Agent 基础 CRUD。
- Agent 默认模型引用。
- 系统提示词与开场白配置。
- 模型参数与运行参数保存。
- 工具 ID 绑定。
- 知识库 ID 绑定。
- Agent 配置预览。
- 前端单页管理。

一期不做：

- Workflow 节点/边/版本管理。
- 真实 Agent 试跑。
- SSE 对话执行。
- 工具和知识库强外键约束。
- 工具参数复杂编排 UI。
- Agent 发布版本管理。

## 3. 核心设计原则

### 3.1 Agent 是配置主体，不是编排执行器

Agent 模块只负责保存和输出配置。

执行链路由 `conversation` 模块负责：

- 加载 Agent 配置。
- 解析默认模型。
- 执行知识库检索。
- 执行工具调用。
- 调用 LLM。
- 保存对话日志。

这样可以避免把 orchestration 逻辑提前塞进 `agent` 模块，保持现有后端分层约束。

### 3.2 聚合读写优先

前端是一个“Agent 配置”页面，后端采用聚合接口：

- 列表读取 Agent 摘要。
- 详情读取完整聚合配置。
- 创建和更新时一次性提交主体、工具绑定和知识库绑定。

内部仍然保留表结构分层：

- `agents`
- `agent_tool_bindings`
- `agent_knowledge_bindings`

### 3.3 为 Workflow 预留，不提前实现 Workflow

当前通过以下字段预留扩展：

- `orchestration_mode`
- `workflow_ref_json`
- `runtime_config_json`

一期允许保存 `orchestrationMode = workflow` 的草稿，但不允许启用为 `active`。

未来 Workflow 模块落地后，可新增独立的 Workflow 表，并让 Agent 指向某个 Workflow definition/version。

## 4. 当前实现状态

已完成：

- Agent 配置数据库迁移。
- 后端 ORM、schema、service、router。
- 聚合 CRUD 接口。
- 配置预览接口。
- 后端接口测试。
- 前端 Agent 配置页面。
- 前端 domain 五件套。
- 前端路由和菜单入口。
- 前端 service/路由测试。

已验证：

- Alembic `upgrade head`。
- 后端 Agent/Provider 聚焦测试。
- 后端 ruff。
- 前端 Agent/App/Provider 聚焦测试。
- 前端 oxlint。
- 前端生产类型检查。
- 本地 API 级 E2E：创建、列表、详情、配置预览、编辑、禁用。

未完成或暂缓：

- in-app browser 插件不可用，未完成可视化浏览器点选验证。
- 工具模块已完成，Agent 保存时会校验启用工具必须存在且为 `enabled`。
- 知识库模块已完成基础能力，但 Agent 保存时仍未对知识库绑定做强存在性校验。
- Workflow 模块未完成，Workflow Agent 只能保存草稿。
- 临时 E2E Agent 记录已按确认软删除。

## 5. 后续扩展方向

Workflow 编排建议独立模块化：

- `workflow_definitions`
- `workflow_versions`
- `workflow_nodes`
- `workflow_edges`
- `workflow_runs`

Agent 可通过 `workflow_ref_json` 或后续结构化字段关联 Workflow。

Agent 运行已经由 `conversation` 承接，后续扩展仍应保持该边界：

- conversation 加载 Agent 配置。
- conversation 解析 `orchestration_mode`。
- 普通 Agent 走 LLM + 工具 + 知识库流程。
- Workflow Agent 走 Workflow runtime。
