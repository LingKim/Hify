# 会话模块方案设计

## 1. 背景

Hify 的核心链路是“创建 Agent → 配置工具/知识 → 对话使用”。Agent 配置模块
已经负责保存可运行配置，会话模块负责把配置真正运行起来。

一期目标直接做真实对话体验：

- 选择一个可运行 Agent。
- 创建会话。
- 发送用户消息。
- 通过 SSE 接收 LLM 流式输出。
- 保存会话、消息和运行记录。
- 会话归属于当前登录用户。
- 登录功能完成前，会话默认归属于系统 seed 的 `root` 用户。

## 2. 一期范围

一期范围：

- 会话 CRUD。
- 当前用户会话隔离。
- root 用户 seed。
- 消息历史读取。
- SSE 流式发送消息。
- LiteLLM 真实调用。
- Agent 可运行性校验。
- 运行状态与错误落库。
- 前端会话页面。

一期不做：

- Workflow 运行。
- 工具调用闭环。
- RAG 检索闭环。
- 附件、多模态、语音输入。
- 多用户协作会话。
- 跨用户会话审计。
- 每个 token 分片落库。

## 3. 核心设计原则

### 3.1 Conversation 是唯一运行编排层

Agent 模块只保存配置。会话运行必须由 `conversation` 完成：

- 加载 Agent。
- 校验模型。
- 拼装系统提示词和历史上下文。
- 调用 LiteLLM。
- 发送 SSE。
- 保存消息和 run。

这样符合后端分层规则，也避免把运行逻辑散落到 Agent、Tool 或 Knowledge 模块。

### 3.2 流式输出和最终落库分离

SSE chunk 面向实时体验，数据库保存最终结果：

- 用户消息先落库。
- assistant 消息先创建为空并标记 `streaming`。
- token 增量直接发给前端，服务端内存累计。
- 完成后一次性更新 assistant 完整内容。
- 异常时更新 run 和 assistant 为 `failed`。

这样能降低数据库写入压力，同时保证刷新页面后历史可恢复。

### 3.3 快照优先

历史会话不能依赖实时 Agent 配置解释，因此创建会话和运行时保存必要快照：

- Agent 名称、模式、运行参数。
- Provider 和 Model 摘要。
- 工具和知识库绑定摘要。

快照不保存 Provider 明文密钥。

## 4. 当前实现状态

已完成：

- Gate 1 产品范围确认：一期直接做 SSE + 真实 LLM 调用。
- Gate 2 数据库设计文档。
- Conversation Alembic 迁移草案。
- Gate 3 API 合约文档。
- Gate 3.5 前端页面拆分文档，明确 `/chat` 和 `/conversations` 两个菜单。

待继续：

- ORM、schema、service、router 实现。
- LiteLLM 流式 executor。
- 后端接口测试。
- 前端会话 domain 和页面。
- 真实 E2E 验证。
