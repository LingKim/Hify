# Agent 工具运行闭环数据库设计

## 1. 设计目标

本阶段目标是把已经存在的工具管理、Agent 工具绑定、会话运行三块数据串成
可验证闭环：

- Agent 可以绑定已启用工具。
- Conversation 运行时可以读取 Agent 绑定工具。
- LLM 触发工具调用后，后端执行 HTTP 工具。
- 工具执行结果可以回喂 LLM，并在会话与工具日志中留下可排查记录。

本期不新增独立工作流、工具编排表或多步骤计划表。工具调用仍属于
`conversation` 运行编排的一部分，`tool` 模块继续只负责工具定义、单次 HTTP
执行和执行日志。

## 2. 实体关系概览

```text
agents
  └── agent_tool_bindings
        └── tools
              ├── tool_parameters
              ├── tool_auth_secrets
              └── tool_execution_logs

conversation_sessions
  ├── conversation_runs
  │     └── tool_execution_logs
  └── conversation_messages
        └── tool_call_json
```

说明：

- `agent_tool_bindings` 决定运行时允许模型调用哪些工具。
- `tools`、`tool_parameters`、`tool_auth_secrets` 作为 tool schema 和真实 HTTP
  执行的配置来源。
- `conversation_runs` 保存一次用户消息触发的整体运行摘要。
- `conversation_messages.tool_call_json` 保存与 assistant 消息相关的工具调用摘要。
- `tool_execution_logs` 保存每次真实 HTTP 调用明细，`source = conversation`
  表示来自 Agent 对话运行。

## 3. 表复用策略

### 3.1 `agent_tool_bindings`

现有字段可满足本期需求：

| 字段 | 用途 |
|---|---|
| `agent_id` | 所属 Agent。 |
| `tool_id` | 绑定的工具，已通过迁移补充到 `tools.id` 的外键。 |
| `binding_name` | 可选运行别名；为空时使用工具名称。 |
| `is_enabled` | 是否在运行时暴露给 LLM。 |
| `sort_order` | 工具展示和 schema 输出顺序。 |
| `config_json` | 单 Agent 对工具的覆盖配置预留。 |
| `metadata_json` | 扩展信息。 |
| `deleted_at` | 软删除绑定。 |

运行规则：

- 新增或启用绑定时，`tool_id` 必须指向未删除且 `status = enabled` 的工具。
- 运行时只加载 `deleted_at IS NULL AND is_enabled = true` 的绑定。
- 如果历史绑定指向已禁用或已归档工具，运行时不暴露给 LLM，并在 runtime
  preview 中返回警告。
- `binding_name` 可作为 LLM tool name 的来源，但必须规范化为只包含字母、
  数字、下划线和短横线；为空或非法时使用基于工具 ID 的稳定名称。

### 3.2 `tools`

现有字段可作为工具定义来源：

| 字段 | 用途 |
|---|---|
| `name` / `description` | 生成 LLM tool 描述。 |
| `status` | 只有 `enabled` 工具可被运行时调用。 |
| `http_method` / `url` | HTTP 执行目标。 |
| `timeout_seconds` | 单次调用超时。 |
| `headers_template_json` | 非密钥请求头模板。 |
| `query_template_json` | 查询参数模板。 |
| `body_template_json` | JSON 请求体模板。 |
| `content_type` | 请求体类型。 |
| `last_test_*` | 保留给管理页测试状态，不被 conversation 调用覆盖。 |

运行规则：

- Conversation 调用工具不更新 `tools.last_test_*`，避免把真实会话调用误认为管理页测试。
- 工具 URL 安全校验沿用现有 `ToolService` 规则。
- 工具密钥只从 `tool_auth_secrets` 解密注入请求，不能写入 conversation
  message、run 或 SSE 事件。

### 3.3 `tool_parameters`

现有字段可生成 LLM tool input schema：

| 字段 | 用途 |
|---|---|
| `name` | LLM tool 参数名。 |
| `label` / `description` | 参数说明。 |
| `param_location` | 参数在 HTTP 请求中的位置。 |
| `schema_type` | JSON schema 基础类型。 |
| `is_required` | 是否必填。 |
| `default_value_json` | 缺省值。 |
| `enum_values_json` | 枚举值。 |
| `schema_json` | 更完整的 JSON schema 片段。 |
| `sort_order` | 参数输出顺序。 |

运行规则：

- 生成 LLM schema 时，`schema_json` 优先；为空时根据 `schema_type`、
  `description`、`enum_values_json` 组装。
- 必填参数缺失时，不猜测默认值；工具调用失败，并通过 SSE 返回
  `tool.failed`。
- `header` 参数只允许普通业务 header，不允许作为密钥通道；密钥仍只走
  `tool_auth_secrets`。

### 3.4 `tool_execution_logs`

现有字段是本期工具调用明细的主记录：

| 字段 | 用途 |
|---|---|
| `tool_id` | 被调用工具。 |
| `executor_user_id` | 当前登录用户。 |
| `conversation_id` | 关联会话。 |
| `run_id` | 关联本轮 conversation run。 |
| `source` | 固定写入 `conversation`。 |
| `status` | `success`、`failed` 或 `timeout`。 |
| `request_method` / `request_url` | 执行请求摘要。 |
| `request_headers_json` | 脱敏后的请求头。 |
| `request_body_preview` | 截断后的请求体摘要。 |
| `response_status_code` | 上游 HTTP 状态码。 |
| `response_headers_json` | 脱敏后的响应头。 |
| `response_body_preview` | 截断后的响应体摘要。 |
| `latency_ms` | 调用耗时。 |
| `error_code` / `error_message` | 失败原因。 |
| `metadata_json` | 保存 LLM tool call ID、tool name、参数摘要等。 |

写入规则：

- 每次真实 HTTP 工具调用必须写一条 `tool_execution_logs`。
- `source = conversation` 时，必须写入 `conversation_id` 和 `run_id`。
- 请求和响应预览继续遵守现有截断策略，避免大响应撑爆数据库。
- `request_headers_json` 和 `response_headers_json` 必须脱敏
  `Authorization`、API key、cookie 等敏感字段。
- `metadata_json` 建议结构：

```json
{
  "toolCallId": "call_xxx",
  "runtimeToolName": "weather_lookup",
  "argumentsPreview": {
    "city": "Hangzhou"
  }
}
```

### 3.5 `conversation_runs`

现有 JSON 字段可保存本轮整体工具调用摘要，不新增列：

| 字段 | 用途 |
|---|---|
| `request_json` | 保存暴露给 LLM 的工具列表摘要、RAG 摘要和用户消息上下文统计。 |
| `response_json` | 保存最终模型输出摘要和工具调用汇总。 |
| `error_json` | 保存导致本轮失败的模型或工具错误。 |
| `metadata_json` | 保存运行时诊断信息。 |

建议 `response_json.toolCalls` 结构：

```json
{
  "toolCalls": [
    {
      "toolCallId": "call_xxx",
      "toolId": 1,
      "toolName": "查询天气",
      "runtimeToolName": "weather_lookup",
      "status": "success",
      "executionLogId": 10,
      "latencyMs": 320,
      "responseStatusCode": 200,
      "responsePreview": "{\"temperature\": 26}"
    }
  ]
}
```

### 3.6 `conversation_messages`

现有 `tool_call_json` 可作为 assistant 消息的工具调用摘要，不新增列。

建议 `tool_call_json` 结构：

```json
{
  "calls": [
    {
      "toolCallId": "call_xxx",
      "toolId": 1,
      "toolName": "查询天气",
      "runtimeToolName": "weather_lookup",
      "status": "success",
      "executionLogId": 10,
      "argumentsPreview": {
        "city": "Hangzhou"
      },
      "responsePreview": "{\"temperature\": 26}",
      "latencyMs": 320
    }
  ]
}
```

读取规则：

- 前端消息响应可从 `tool_call_json.calls` 派生 `toolCalls` 字段。
- `responsePreview` 只用于 UI 摘要，不作为再次执行的依据。
- 失败调用也要写入 `tool_call_json`，便于用户知道回答为什么退化。

## 4. 状态与生命周期

### 4.1 工具绑定生命周期

- `active`：`agent_tool_bindings.deleted_at IS NULL AND is_enabled = true`。
- `disabled`：绑定存在但 `is_enabled = false`。
- `deleted`：`deleted_at IS NOT NULL`，运行时忽略。

工具自身状态仍以 `tools.status` 为准：

- `enabled`：可被新绑定和运行时调用。
- `draft` / `disabled` / `archived`：不可被新绑定；历史绑定运行时忽略或提示不可用。

### 4.2 工具调用生命周期

一次 conversation 工具调用建议经历：

1. LLM 返回 tool call。
2. Conversation 发送 SSE `tool.started`。
3. ToolService 执行 HTTP 请求并写入 `tool_execution_logs`。
4. Conversation 发送 `tool.completed` 或 `tool.failed`。
5. Conversation 把工具结果作为 tool message 回喂 LLM。
6. LLM 输出最终 assistant 文本。
7. Conversation 更新 `conversation_runs.response_json` 和
   `conversation_messages.tool_call_json`。

## 5. 约束、索引与外键

本期沿用现有约束：

- `agent_tool_bindings.tool_id -> tools.id` 已存在。
- `tool_execution_logs.tool_id -> tools.id` 已存在。
- `tool_execution_logs.executor_user_id -> users.id` 已存在。
- `tool_execution_logs.conversation_id` 和 `run_id` 已有索引，但当前没有外键。

本期不新增 `tool_execution_logs.conversation_id` 和 `run_id` 外键。原因：

- 现有迁移已把这两个字段作为可选追踪字段。
- 工具日志也服务测试执行，测试执行不一定有 conversation/run。
- 后续如果需要强一致，可单独补迁移添加可空外键。

## 6. 迁移策略

本期建议 **不新增 Alembic 迁移**。

理由：

- 工具运行闭环所需的主体表、绑定表、参数表、密钥表、执行日志表已经存在。
- `conversation_runs` 已有 `request_json`、`response_json`、`error_json`、
  `metadata_json`。
- `conversation_messages` 已有 `tool_call_json` 和 `metadata_json`。
- `tool_execution_logs` 已有 `conversation_id`、`run_id`、`source`、`metadata_json`。

实现阶段只需要：

- 在 ORM 和 schema 层明确读写 JSON 结构。
- 在 service 层补充运行时校验和写入规则。
- 在测试中覆盖 JSON 结构和日志记录。

## 7. Seed 与回填

本期不需要 seed 或历史数据回填。

已有 Agent 工具绑定如果指向不存在的工具，已在工具迁移中被清理；如果指向已禁用
或归档工具，运行时按不可用处理，不做批量修改。

## 8. 风险与后续扩展

风险：

- JSON 字段缺少数据库级 schema 约束，需要通过 Pydantic schema 和测试保证结构。
- 多轮工具调用时，单个 `tool_call_json` 可能变大，需要限制调用轮数和预览长度。
- 如果后续要按工具调用做复杂统计，仅靠 JSON 摘要不够，需要独立
  `conversation_tool_calls` 表。

后续扩展触发条件：

- 需要展示完整调用链、支持重放、按调用步骤筛选时，新增
  `conversation_tool_calls`。
- 需要多轮工具调用和 planner 诊断时，新增 run step 表或 workflow run 表。
- 需要强一致查询时，为 `tool_execution_logs.conversation_id` 和 `run_id`
  补可空外键。
