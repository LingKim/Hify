# 会话模块接口设计

## 1. 设计目标

会话接口一期直接服务真实对话运行：

- 前端可以创建会话、读取会话列表、读取消息历史、删除或归档会话。
- 用户发送消息时，后端通过 SSE 流式返回 LLM 输出。
- 后端在 `conversation` 编排层加载 Agent 配置、解析 Provider/Model、调用
  LiteLLM，并保存用户消息、assistant 消息和运行记录。
- 普通 JSON 接口继续使用项目统一 `Result<T>` / `PageResult<T>` envelope。
- SSE 接口使用 `text/event-stream`，事件 payload 为 JSON，但不包一层
  `Result`。

## 2. 命名和通用约定

字段命名：

- HTTP JSON 使用 camelCase。
- Python schema 内部使用 snake_case，通过 Pydantic alias 输出 camelCase。
- 时间字段使用 ISO 8601 字符串。
- ID 字段保留为 number，不把内部 ID 暴露成用户手填字段。
- 会话接口需要登录态，后端通过 `get_current_user` 获取当前用户。
- 一期所有会话查询、继续、归档、删除都按当前用户隔离，不允许跨用户访问。
- 登录功能完成前，后端使用系统 seed 的 `root` 用户作为默认当前用户。

分页：

- `page`：页码，默认 `1`。
- `pageSize`：每页数量，默认 `20`，最大 `100`。
- 响应使用 `PageResult<T>`：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [],
    "total": 0,
    "page": 1,
    "pageSize": 20,
    "totalPages": 0
  }
}
```

## 3. 接口列表

### 3.1 获取会话列表

`GET /api/v1/conversations`

说明：

- 返回当前可见会话摘要列表。
- 默认只返回未软删除会话。
- 默认只返回当前登录用户的会话。
- 默认按 `lastMessageAt DESC, updatedAt DESC` 排序。

查询参数：

- `page`
- `pageSize`
- `keyword`：按标题、最后消息摘要模糊搜索。
- `agentId`：按 Agent 过滤。
- `status`：按会话状态过滤，允许 `active`、`archived`。
- `includeArchived`：是否包含归档会话，默认 `false`。

响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1001,
        "userId": 1,
        "agentId": 12,
        "agentName": "客服助手",
        "title": "售后政策咨询",
        "status": "active",
        "channel": "web",
        "lastMessageRole": "assistant",
        "lastMessagePreview": "根据当前售后政策，7 天内可以申请退换。",
        "lastMessageAt": "2026-05-05T11:30:00Z",
        "messageCount": 6,
        "createdAt": "2026-05-05T11:00:00Z",
        "updatedAt": "2026-05-05T11:30:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "pageSize": 20,
    "totalPages": 1
  }
}
```

### 3.2 创建会话

`POST /api/v1/conversations`

说明：

- 基于一个可运行 Agent 创建会话。
- 会话所属用户来自当前登录态，不接受前端传 `userId`。
- 登录功能完成前，所有新建会话先归属 `root` 用户。
- 后端校验 Agent 必须存在、未删除、`status = active`。
- 后端校验 Agent 必须绑定可用 Provider Model，且模型支持 chat。
- 创建时保存 Agent 快照。
- 如果 Agent 配置了 `openingMessage`，后端可返回但不强制落为一条消息；
  一期推荐作为 `openingMessage` 字段返回，由前端空会话态展示。

请求体：

```json
{
  "agentId": 12,
  "title": "售后政策咨询",
  "channel": "web",
  "metadata": null
}
```

字段规则：

- `agentId`：必填，必须大于 0。
- `title`：可选，空时由后端生成 `新会话`，首条消息发送后可自动更新标题。
- `channel`：可选，默认 `web`。
- `metadata`：可选扩展字段。

响应示例：

```json
{
  "code": 201,
  "message": "success",
  "data": {
    "id": 1001,
    "userId": 1,
    "agentId": 12,
    "agentName": "客服助手",
    "title": "售后政策咨询",
    "status": "active",
    "channel": "web",
    "openingMessage": "你好，我可以帮你查询产品和订单问题。",
    "agentSnapshot": {
      "agentId": 12,
      "name": "客服助手",
      "orchestrationMode": "agent",
      "providerInstanceId": 2,
      "providerModelId": 8,
      "modelName": "gpt-4.1-mini",
      "displayName": "GPT-4.1 Mini"
    },
    "lastMessageRole": null,
    "lastMessagePreview": null,
    "lastMessageAt": null,
    "messageCount": 0,
    "createdAt": "2026-05-05T11:00:00Z",
    "updatedAt": "2026-05-05T11:00:00Z"
  }
}
```

### 3.3 获取会话详情

`GET /api/v1/conversations/{conversation_id}`

说明：

- 返回单个会话详情，不包含完整消息列表。
- 前端进入页面后并行调用详情和消息列表。
- 如果会话不属于当前用户，返回 `7001 CONVERSATION_NOT_FOUND`，避免泄露存在性。

路径参数：

- `conversation_id`：会话 ID。

响应结构同创建会话响应。

### 3.4 更新会话

`PATCH /api/v1/conversations/{conversation_id}`

说明：

- 一期只允许更新标题和状态。
- 状态可用于归档或恢复。
- `/chat` 会话列表中的删除 icon 调用本接口把状态改为 `archived`，不是软删除。

请求体：

```json
{
  "title": "新的会话标题",
  "status": "archived"
}
```

字段规则：

- `title`：可选，1-255 字符。
- `status`：可选，允许 `active`、`archived`。

响应结构同创建会话响应。

### 3.5 删除会话

`DELETE /api/v1/conversations/{conversation_id}`

说明：

- 软删除会话。
- 服务层同步软删除消息和运行记录。
- 该接口只在 `会话日志` 管理页使用；`对话使用` 页的删除 icon 不调用该接口。

响应：

- `204 No Content`

### 3.6 获取消息列表

`GET /api/v1/conversations/{conversation_id}/messages`

说明：

- 返回某个会话的消息历史。
- 默认按 `sequence ASC` 排序。
- 一期消息量不大时可分页；前端默认请求最近 100 条。
- 如果会话不属于当前用户，返回 `7001 CONVERSATION_NOT_FOUND`。

查询参数：

- `page`
- `pageSize`
- `role`：可选，按角色过滤。

响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 5001,
        "conversationId": 1001,
        "runId": 9001,
        "role": "user",
        "status": "completed",
        "content": "退货政策是什么？",
        "contentFormat": "text",
        "sequence": 1,
        "tokenCount": null,
        "latencyMs": null,
        "modelSnapshot": null,
        "error": null,
        "createdAt": "2026-05-05T11:10:00Z",
        "updatedAt": "2026-05-05T11:10:00Z"
      },
      {
        "id": 5002,
        "conversationId": 1001,
        "runId": 9001,
        "role": "assistant",
        "status": "completed",
        "content": "根据当前售后政策，7 天内可以申请退换。",
        "contentFormat": "text",
        "sequence": 2,
        "tokenCount": 32,
        "latencyMs": 1280,
        "modelSnapshot": {
          "providerInstanceId": 2,
          "providerModelId": 8,
          "modelName": "gpt-4.1-mini",
          "displayName": "GPT-4.1 Mini"
        },
        "error": null,
        "createdAt": "2026-05-05T11:10:00Z",
        "updatedAt": "2026-05-05T11:10:02Z"
      }
    ],
    "total": 2,
    "page": 1,
    "pageSize": 100,
    "totalPages": 1
  }
}
```

### 3.7 SSE 发送消息

`POST /api/v1/conversations/{conversation_id}/messages/stream`

说明：

- 用户发送一条消息，并通过 SSE 接收 assistant 回复。
- 只能向当前用户自己的 active 会话发送消息。
- 后端必须先持久化 user 消息、run 记录、assistant 占位消息，再开始调用
  LiteLLM。
- 端点返回 `text/event-stream`。
- 该接口不使用 `Result` envelope。
- 前端不能通过通用 `request<T>()` 调用，应使用会话 domain 内的专用 SSE
  service。
- 因为接口是 `POST`，前端必须使用 `fetch` 手动读取响应流，不使用
  `EventSource`。

请求头：

- `Accept: text/event-stream`
- `Content-Type: application/json`

请求体：

```json
{
  "content": "退货政策是什么？",
  "metadata": null
}
```

字段规则：

- `content`：必填，trim 后不能为空，最大 20000 字符。
- `metadata`：可选扩展字段。

SSE 通用格式：

```text
event: message.delta
data: {"runId":9001,"messageId":5002,"delta":"根据当前"}

```

事件列表：

| event | 说明 |
|---|---|
| `run.started` | 运行已创建并开始 |
| `message.created` | user 与 assistant 消息已创建 |
| `message.delta` | assistant 增量文本 |
| `message.completed` | assistant 消息完成 |
| `run.completed` | run 完成并写入统计 |
| `done` | 本轮 SSE 正常结束，前端可恢复输入 |
| `error` | 本次运行失败 |

`run.started` 示例：

```json
{
  "runId": 9001,
  "conversationId": 1001,
  "status": "running",
  "startedAt": "2026-05-05T11:10:00Z"
}
```

`message.created` 示例：

```json
{
  "userMessage": {
    "id": 5001,
    "role": "user",
    "status": "completed",
    "content": "退货政策是什么？",
    "sequence": 1,
    "createdAt": "2026-05-05T11:10:00Z"
  },
  "assistantMessage": {
    "id": 5002,
    "role": "assistant",
    "status": "streaming",
    "content": "",
    "sequence": 2,
    "createdAt": "2026-05-05T11:10:00Z"
  }
}
```

`message.delta` 示例：

```json
{
  "runId": 9001,
  "messageId": 5002,
  "delta": "根据当前",
  "sequence": 1
}
```

`message.completed` 示例：

```json
{
  "runId": 9001,
  "message": {
    "id": 5002,
    "role": "assistant",
    "status": "completed",
    "content": "根据当前售后政策，7 天内可以申请退换。",
    "contentFormat": "text",
    "sequence": 2,
    "tokenCount": 32,
    "latencyMs": 1280,
    "updatedAt": "2026-05-05T11:10:02Z"
  }
}
```

`run.completed` 示例：

```json
{
  "runId": 9001,
  "status": "completed",
  "latencyMs": 1280,
  "inputTokenCount": 18,
  "outputTokenCount": 32,
  "totalTokenCount": 50,
  "completedAt": "2026-05-05T11:10:02Z"
}
```

`done` 示例：

```json
{
  "runId": 9001,
  "conversationId": 1001
}
```

`error` 示例：

```json
{
  "runId": 9001,
  "messageId": 5002,
  "code": 3003,
  "message": "模型调用鉴权失败",
  "status": "failed",
  "retryable": false
}
```

SSE 错误语义：

- 如果错误发生在 SSE 响应开始前，返回普通 JSON 错误 envelope。
- 如果错误发生在 SSE 响应开始后，发送 `event: error`，随后关闭连接。
- 后端必须把 run 和 assistant 消息标记为 `failed` 并写入 `errorJson`。

### 3.8 Agent 可运行预览

`GET /api/v1/conversations/agents/{agent_id}/runtime-preview`

说明：

- 给会话页选择 Agent 时使用。
- 比 Agent 模块已有 config preview 更贴近运行态。
- 该接口由 `conversation` 模块提供，因为真实运行校验属于编排层。

路径参数：

- `agent_id`：Agent ID。

响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "agentId": 12,
    "name": "客服助手",
    "status": "active",
    "orchestrationMode": "agent",
    "isRunnable": true,
    "blockedReason": null,
    "model": {
      "providerInstanceId": 2,
      "providerName": "OpenAI-生产",
      "providerType": "openai",
      "modelId": 8,
      "modelName": "gpt-4.1-mini",
      "displayName": "GPT-4.1 Mini",
      "supportsStream": true
    },
    "openingMessage": "你好，我可以帮你查询产品和订单问题。",
    "enabledToolIds": [],
    "enabledKnowledgeBaseIds": []
  }
}
```

## 4. 错误码与校验规则

沿用现有错误码：

- `7001 CONVERSATION_NOT_FOUND`：会话不存在或已删除。
- `7002 AGENT_MODEL_NOT_CONFIGURED`：Agent 不可运行、未绑定模型、模型不存在或
  不支持 chat/stream。
- `7003 SSE_CONNECTION_ERROR`：SSE 建连或流式输出异常。
- `7004 EMPTY_MESSAGE_CONTENT`：用户消息为空。
- `7005 CONVERSATION_CLOSED`：会话已归档、关闭或不可继续。

复用跨模块错误码：

- `4001 AGENT_NOT_FOUND`
- `4002 INVALID_CONFIGURATION`
- `3001 MODEL_NOT_FOUND`
- `3003 PROVIDER_AUTH_FAILED`
- `3004 REQUEST_TIMEOUT`
- `3005 PROVIDER_RATE_LIMITED`
- `3007 INVALID_MODEL_PARAMETERS`

校验规则：

- 创建会话时 Agent 必须为 `active`。
- Workflow Agent 一期不能运行；如果 `orchestrationMode = workflow`，返回
  `4002 INVALID_CONFIGURATION` 或 `7002 AGENT_MODEL_NOT_CONFIGURED`。
- 模型必须存在且未软删除。
- 模型必须 `supportsChat = true`。
- SSE 一期要求 `supportsStream = true`；不自动降级到非流式，避免前端体验不一致。
- 用户消息 trim 后不能为空。
- 已归档会话不能继续发送消息。
- 会话不属于当前用户时按不存在处理。

## 5. 前端契约

新增 domain：

```text
frontend/src/domain/conversation/
├── types.ts
├── api.ts
├── service.ts
├── queries.ts
└── components.tsx
```

新增页面：

```text
frontend/src/pages/chat/ChatPage.tsx
frontend/src/pages/conversation/ConversationLogPage.tsx
```

新增路由：

- `/chat`
- `/conversations`

服务层约定：

- JSON 接口使用 `request<T>()`。
- SSE 接口使用专用函数，例如 `streamConversationMessage()`。
- SSE service 负责解析事件并通过回调通知组件：
  - `onRunStarted`
  - `onMessageCreated`
  - `onDelta`
  - `onMessageCompleted`
  - `onRunCompleted`
  - `onDone`
  - `onError`
- 组件收到 `message.delta` 时只更新前端临时文本；收到
  `message.completed` 后用后端最终消息覆盖本地状态。
- 输入框提交后可以立即清空，但前端必须保留本轮 `submittedContent`，用于
  SSE 请求失败或 `error` 事件后的重试。

## 6. 实现兼容说明

- LiteLLM 目前已有非流式 `invoke_text`，需要在 `llm.executor` 增加流式执行
  方法，但调用入口仍由 `conversation.service` 编排。
- `conversation` 可以 import `agent.service` 和 `llm.service/executor`，符合
  后端分层规则。
- 不把真实运行逻辑放入 `agent`、`tool` 或 `knowledge`。
- 一期工具和知识库绑定只进入 Agent 快照和请求上下文预留，不强制执行工具或
  RAG。

## 7. 验收标准

- 创建会话接口能拒绝不可运行 Agent。
- SSE 发送消息能按顺序返回 `run.started`、`message.created`、
  `message.delta`、`message.completed`、`run.completed`、`done`。
- LLM 鉴权失败、限流、超时能通过 SSE `error` 返回，并落库为 failed。
- 刷新页面后能通过消息列表看到最终 user/assistant 历史。
- 删除会话后列表和详情不可见。
- 前端不用通用 `request<T>()` 处理 SSE。
