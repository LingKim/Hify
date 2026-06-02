# Agent 工具运行闭环接口设计

## 1. 设计目标

本接口设计服务一个核心链路：

`Agent 绑定工具 -> 对话运行时暴露工具 -> LLM 触发工具调用 -> 后端执行 HTTP 工具 -> 工具结果回喂 LLM -> SSE 输出最终回答`

本期尽量复用已有接口，不新增独立工具运行资源。运行编排继续由
`conversation` 模块负责，`tool` 模块继续提供工具定义、选项列表、单次执行和
执行日志能力。

## 2. 通用约定

- 普通 JSON 接口继续使用 `Result<T>` envelope。
- SSE 接口继续使用 `text/event-stream`，事件 payload 为 JSON，不包
  `Result`。
- HTTP JSON 字段使用 camelCase。
- 工具密钥、密文、明文 Authorization、Cookie、API Key 不允许出现在任何
  conversation 响应、SSE 事件或消息历史响应中。
- 本期运行时最多执行一轮 tool call。模型一次返回多个 tool call 时，按数组顺序
  串行执行；执行后统一回喂 LLM 生成最终回答。
- 如果工具执行失败，本轮 SSE 不直接崩溃。后端发送 `tool.failed`，并把失败结果
  回喂 LLM，让 assistant 生成可读回答；只有模型调用、会话状态、权限等核心错误
  才发送 SSE `error` 并终止。

## 3. 复用接口

### 3.1 获取工具选项

```text
GET /api/v1/tools/options
```

用途：

- Agent 配置页工具选择器。
- 只展示可被新绑定的工具。

查询参数：

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `keyword` | string | - | 按工具名称或 URL 模糊搜索。 |
| `status` | string | `enabled` | 本期 Agent 选择器固定传 `enabled`。 |

响应：

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "查询天气",
      "description": "按城市查询天气",
      "status": "enabled",
      "httpMethod": "GET",
      "url": "https://api.example.com/weather",
      "parameterCount": 1
    }
  ]
}
```

兼容说明：

- 该接口已存在，本期不改路径。
- 如后端已经支持 `status` alias，前端必须使用 `status=enabled`，不要再使用
  `statusValue`。

### 3.2 创建或更新 Agent 工具绑定

```text
POST /api/v1/agents
PUT /api/v1/agents/{agent_id}
```

请求体中的 `tools` 字段继续复用 Agent 配置契约：

```json
{
  "tools": [
    {
      "toolId": 1,
      "bindingName": null,
      "isEnabled": true,
      "sortOrder": 0,
      "config": null,
      "metadata": null
    }
  ]
}
```

校验规则：

- `toolId` 必须大于 0。
- 同一个 Agent 内 `toolId` 不能重复。
- 新增绑定或把绑定改为 `isEnabled = true` 时，工具必须存在、未软删除且
  `status = enabled`。
- 如果编辑旧 Agent 时已有绑定工具变成 `disabled` 或 `archived`：
  - 后端允许保存为 `isEnabled = false`。
  - 如果仍提交 `isEnabled = true`，返回业务错误。
- 前端不允许让用户手填工具 ID，必须通过工具选项接口选择。

错误：

- `4002 INVALID_CONFIGURATION`：工具不存在、不可绑定、重复绑定或配置非法。
- `6001 TOOL_NOT_FOUND`：工具不存在或已删除。

### 3.3 Agent 运行预览

```text
GET /api/v1/conversations/agents/{agent_id}/runtime-preview
```

用途：

- 会话页选择 Agent 后，展示运行可用性。
- 前端判断是否允许发送消息。
- 告知用户当前 Agent 暴露了哪些工具。

响应新增 `tools` 与 `warnings`，保留现有 `enabledToolIds` 兼容字段：

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
      "providerName": "DeepSeek",
      "providerType": "deepseek",
      "modelId": 8,
      "modelName": "deepseek-chat",
      "displayName": "DeepSeek Chat",
      "supportsStream": true
    },
    "openingMessage": "你好，我可以帮你查询信息。",
    "enabledToolIds": [1],
    "enabledKnowledgeBaseIds": [],
    "tools": [
      {
        "toolId": 1,
        "toolName": "查询天气",
        "runtimeToolName": "weather_lookup",
        "description": "按城市查询天气",
        "status": "enabled",
        "httpMethod": "GET",
        "parameterCount": 1
      }
    ],
    "warnings": []
  }
}
```

字段说明：

| 字段 | 说明 |
|---|---|
| `enabledToolIds` | 兼容旧前端，只返回运行时启用且可用的工具 ID。 |
| `tools` | 运行时实际会暴露给 LLM 的工具摘要。 |
| `runtimeToolName` | 传给 LLM 的工具名，必须稳定且符合 provider 命名限制。 |
| `warnings` | 历史绑定工具不可用、模型不支持工具等非阻断提示。 |

模型支持规则：

- 本期要求模型配置 `supportsTools = true` 才暴露工具。
- 如果模型不支持工具但 Agent 绑定了工具：
  - `isRunnable` 仍可为 true，只是不暴露工具。
  - `warnings` 返回“当前模型不支持工具调用，已忽略工具绑定”。

## 4. SSE 发送消息扩展

### 4.1 端点

```text
POST /api/v1/conversations/{conversation_id}/messages/stream
```

请求体沿用现有契约：

```json
{
  "content": "帮我查一下杭州今天适不适合露营",
  "metadata": null
}
```

### 4.2 事件顺序

无工具调用时，保持现有顺序：

```text
run.started
message.created
message.delta*
message.completed
run.completed
done
```

有工具调用时，顺序扩展为：

```text
run.started
message.created
tool.started
tool.completed | tool.failed
message.delta*
message.completed
run.completed
done
```

如果模型一次返回多个 tool call：

```text
tool.started
tool.completed | tool.failed
tool.started
tool.completed | tool.failed
message.delta*
```

如果工具执行失败：

- 发送 `tool.failed`。
- 后端把失败摘要作为 tool result 回喂 LLM。
- 后续仍尽量输出 `message.delta` 和 `message.completed`。
- 只有 LLM 二次生成也失败时，发送 `error` 并终止。

### 4.3 `tool.started`

说明：后端准备执行一个工具调用。

```json
{
  "runId": 9001,
  "conversationId": 1001,
  "messageId": 5002,
  "toolCallId": "call_abc",
  "toolId": 1,
  "toolName": "查询天气",
  "runtimeToolName": "weather_lookup",
  "argumentsPreview": {
    "city": "Hangzhou"
  },
  "startedAt": "2026-05-24T10:00:00Z"
}
```

字段规则：

- `argumentsPreview` 必须脱敏并限制大小。
- 如果参数包含明显敏感字段，如 `token`、`password`、`secret`，值必须替换为
  `***`。

### 4.4 `tool.completed`

说明：工具执行成功。

```json
{
  "runId": 9001,
  "conversationId": 1001,
  "messageId": 5002,
  "toolCallId": "call_abc",
  "toolId": 1,
  "toolName": "查询天气",
  "runtimeToolName": "weather_lookup",
  "status": "success",
  "executionLogId": 3001,
  "latencyMs": 328,
  "responseStatusCode": 200,
  "responsePreview": "{\"weather\":\"sunny\",\"temperature\":26}",
  "completedAt": "2026-05-24T10:00:01Z"
}
```

字段规则：

- `responsePreview` 是截断摘要，不保证是完整 JSON。
- 前端只把 `responsePreview` 当作 UI 摘要展示，不用于业务解析。

### 4.5 `tool.failed`

说明：工具执行失败，但本轮对话不一定失败。

```json
{
  "runId": 9001,
  "conversationId": 1001,
  "messageId": 5002,
  "toolCallId": "call_abc",
  "toolId": 1,
  "toolName": "查询天气",
  "runtimeToolName": "weather_lookup",
  "status": "failed",
  "executionLogId": 3002,
  "latencyMs": 1000,
  "errorCode": "TOOL_HTTP_ERROR",
  "errorMessage": "上游接口返回 500",
  "retryable": true,
  "completedAt": "2026-05-24T10:00:01Z"
}
```

字段规则：

- `retryable = true` 只表示该工具调用理论上可重试，不表示前端自动重试。
- 如果失败发生在参数校验阶段且没有写入工具日志，`executionLogId` 可以为
  `null`。

### 4.6 `message.completed` 扩展

`message.completed.message` 新增 `toolCalls`，保留现有字段：

```json
{
  "runId": 9001,
  "message": {
    "id": 5002,
    "role": "assistant",
    "status": "completed",
    "content": "杭州今天晴，气温 26 度，适合露营。",
    "contentFormat": "text",
    "sequence": 2,
    "tokenCount": 64,
    "latencyMs": 1880,
    "knowledgeSources": [],
    "toolCalls": [
      {
        "toolCallId": "call_abc",
        "toolId": 1,
        "toolName": "查询天气",
        "runtimeToolName": "weather_lookup",
        "status": "success",
        "executionLogId": 3001,
        "argumentsPreview": {
          "city": "Hangzhou"
        },
        "responsePreview": "{\"weather\":\"sunny\",\"temperature\":26}",
        "latencyMs": 328
      }
    ],
    "updatedAt": "2026-05-24T10:00:02Z"
  }
}
```

## 5. 消息历史响应扩展

### 5.1 获取消息列表

```text
GET /api/v1/conversations/{conversation_id}/messages
```

`ConversationMessageResp` 新增 `toolCalls` 字段：

```json
{
  "id": 5002,
  "conversationId": 1001,
  "runId": 9001,
  "role": "assistant",
  "status": "completed",
  "content": "杭州今天晴，气温 26 度，适合露营。",
  "contentFormat": "text",
  "sequence": 2,
  "tokenCount": 64,
  "latencyMs": 1880,
  "modelSnapshot": {
    "providerInstanceId": 2,
    "providerModelId": 8,
    "modelName": "deepseek-chat",
    "displayName": "DeepSeek Chat"
  },
  "error": null,
  "knowledgeSources": [],
  "toolCalls": [
    {
      "toolCallId": "call_abc",
      "toolId": 1,
      "toolName": "查询天气",
      "runtimeToolName": "weather_lookup",
      "status": "success",
      "executionLogId": 3001,
      "argumentsPreview": {
        "city": "Hangzhou"
      },
      "responsePreview": "{\"weather\":\"sunny\",\"temperature\":26}",
      "latencyMs": 328
    }
  ],
  "createdAt": "2026-05-24T10:00:00Z",
  "updatedAt": "2026-05-24T10:00:02Z"
}
```

兼容规则：

- 没有工具调用时，`toolCalls` 返回空数组。
- 前端必须兼容旧数据 `toolCalls` 缺失或为空。

### 5.2 Tool call 对象

```json
{
  "toolCallId": "call_abc",
  "toolId": 1,
  "toolName": "查询天气",
  "runtimeToolName": "weather_lookup",
  "status": "success",
  "executionLogId": 3001,
  "argumentsPreview": {
    "city": "Hangzhou"
  },
  "responsePreview": "{\"weather\":\"sunny\",\"temperature\":26}",
  "latencyMs": 328,
  "errorCode": null,
  "errorMessage": null
}
```

字段说明：

| 字段 | 说明 |
|---|---|
| `toolCallId` | LLM 返回的 tool call ID；没有时后端生成稳定 ID。 |
| `toolId` | Hify 工具 ID。 |
| `toolName` | 用户可读工具名。 |
| `runtimeToolName` | 传给 LLM 的工具名。 |
| `status` | `success`、`failed`、`timeout`。 |
| `executionLogId` | 对应 `tool_execution_logs.id`，参数校验失败时可为空。 |
| `argumentsPreview` | 脱敏参数摘要。 |
| `responsePreview` | 成功响应摘要。 |
| `latencyMs` | 工具执行耗时。 |
| `errorCode` / `errorMessage` | 失败原因。 |

## 6. 工具执行日志

### 6.1 获取工具执行日志

```text
GET /api/v1/tools/{tool_id}/execution-logs
```

现有接口继续复用。为了会话日志定位，本期前端可在需要时传：

| 参数 | 说明 |
|---|---|
| `source=conversation` | 只看会话运行产生的工具调用。 |
| `status=success|failed|timeout` | 按执行状态筛选。 |

响应保持现有 `ToolExecutionLogSummaryResp`。如后续需要从会话详情直接打开某条
工具执行明细，再新增按 log ID 的详情接口；本期不新增。

## 7. LLM Tool Schema 契约

后端内部根据 `tools` 和 `tool_parameters` 生成 LiteLLM tools 参数。

示例：

```json
[
  {
    "type": "function",
    "function": {
      "name": "weather_lookup",
      "description": "按城市查询天气",
      "parameters": {
        "type": "object",
        "properties": {
          "city": {
            "type": "string",
            "description": "城市"
          }
        },
        "required": ["city"]
      }
    }
  }
]
```

生成规则：

- `runtimeToolName` 必须唯一。
- 名称来源优先级：`bindingName` -> `tool.name` 规范化 -> `tool_{toolId}`。
- 参数 schema 优先使用 `tool_parameters.schema_json`；为空时用
  `schemaType`、`description`、`enumValues` 生成。
- 只暴露 `status = enabled` 的工具。
- 只暴露 Agent 绑定中 `isEnabled = true` 的工具。

## 8. 错误码与校验规则

复用现有错误码：

- `4002 INVALID_CONFIGURATION`：Agent 工具绑定非法、工具不可用、工具 schema
  生成失败。
- `6001 TOOL_NOT_FOUND`：工具不存在或已删除。
- `6004 TOOL_EXECUTION_FAILED`：工具执行失败。
- `7001 CONVERSATION_NOT_FOUND`：会话不存在。
- `7002 AGENT_MODEL_NOT_CONFIGURED`：Agent 模型不可运行。
- `7005 CONVERSATION_CLOSED`：会话已归档，不能继续发送。
- `3003 PROVIDER_AUTH_FAILED`：模型鉴权失败。
- `3004 REQUEST_TIMEOUT`：模型请求超时。
- `3005 PROVIDER_RATE_LIMITED`：模型限流。
- `3007 INVALID_MODEL_PARAMETERS`：模型参数无效或 provider 不支持当前 tool
  schema。

校验规则：

- Agent 绑定工具时，后端必须校验工具可用性。
- Conversation 运行时，如果绑定工具已不可用，忽略该工具并写入 runtime warning。
- 如果模型不支持工具调用，忽略工具绑定并写入 runtime warning。
- LLM 返回未知 `runtimeToolName` 时，发送 `tool.failed`，不执行任何 HTTP 请求。
- LLM 返回参数不是 JSON object 时，发送 `tool.failed`。
- 必填参数缺失时，发送 `tool.failed`。
- HTTP 工具超时写入 `tool_execution_logs.status = timeout`。
- HTTP 4xx/5xx 默认视为 `failed`，响应摘要仍可回喂 LLM。

## 9. 前端契约

### 9.1 Agent 配置页

文件范围：

```text
frontend/src/domain/agent-configuration/
frontend/src/pages/agent-configuration/AgentConfigurationPage.tsx
frontend/src/domain/tool-integration/service.ts
```

交互：

- 工具字段使用多选，不展示手填 ID。
- 选项来自 `fetchToolOptions({ status: "enabled" })`。
- 选择后提交为 `tools: AgentToolBinding[]`。
- 已有不可用绑定以禁用标签展示，用户保存时应自动转为 `isEnabled = false`
  或提示移除。

### 9.2 Chat 页

文件范围：

```text
frontend/src/domain/conversation/
frontend/src/pages/chat/ChatPage.tsx
```

新增类型：

- `ConversationToolCall`
- `StreamToolStartedEvent`
- `StreamToolCompletedEvent`
- `StreamToolFailedEvent`

`streamConversationMessage()` 新增回调：

- `onToolStarted`
- `onToolCompleted`
- `onToolFailed`

展示规则：

- `tool.started`：在 assistant 气泡下展示“正在调用工具”。
- `tool.completed`：展示工具名、成功状态、耗时、响应摘要。
- `tool.failed`：展示工具名、失败状态和错误信息。
- `message.completed`：用后端最终 `toolCalls` 覆盖本地临时工具状态。

### 9.3 会话日志页

- 消息历史读取 `toolCalls`。
- assistant 消息下展示工具调用摘要。
- 本期不要求做完整工具执行日志详情抽屉。

## 10. 验收标准

- Agent 配置页能从工具选项接口选择 enabled 工具。
- 后端拒绝绑定不存在、已删除、非 enabled 的工具。
- runtime preview 返回 tools 摘要和 warnings。
- SSE 有工具调用时按顺序返回 `tool.started` 和 `tool.completed` 或
  `tool.failed`。
- 工具调用写入 `tool_execution_logs`，且 `source = conversation`。
- `message.completed` 和消息历史都返回 `toolCalls`。
- 工具失败不会直接导致 SSE 崩溃，除非后续模型生成也失败。
- 前端不展示任何密钥、密文、Authorization、Cookie。
- 无工具 Agent 的现有对话链路保持兼容。
