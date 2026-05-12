# Agent 配置接口文档

## 1. 设计目标

Agent 配置接口以“聚合读写”为核心：

- 前端使用一个页面完成 Agent 基础信息、模型、工具、知识库和运行参数配置。
- 后端内部保留 `agents`、`agent_tool_bindings`、`agent_knowledge_bindings` 分层结构。
- 创建和更新接口一次性提交聚合配置，避免前端维护多个半成品子资源状态。
- Agent 模块只提供配置管理，不提供真实执行、SSE、Workflow 编排运行。

真实运行、预览对话、Workflow 执行应由 `conversation` 模块读取 Agent 配置后完成。

## 2. 接口列表

### 2.1 获取 Agent 列表

`GET /api/v1/agents`

说明：

- 返回分页后的 Agent 摘要列表。
- 每项包含基础信息、默认模型摘要、工具数量、知识库数量。
- 默认不返回完整提示词和完整绑定配置，避免列表 payload 过大。

查询参数：

- `page`：页码，默认 `1`。
- `pageSize`：每页数量，默认 `20`，最大 `100`。
- `keyword`：按名称、描述模糊搜索。
- `status`：按状态筛选。
- `orchestrationMode`：按编排模式筛选。
- `providerModelId`：按默认模型筛选。

响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "name": "客服助手",
        "description": "回答售前与售后常见问题",
        "avatarUrl": null,
        "status": "active",
        "orchestrationMode": "agent",
        "providerInstanceId": 1,
        "providerModelId": 3,
        "model": {
          "providerInstanceId": 1,
          "providerName": "OpenAI-生产",
          "providerType": "openai",
          "modelId": 3,
          "modelName": "gpt-4.1",
          "displayName": "GPT-4.1"
        },
        "toolCount": 2,
        "knowledgeBaseCount": 1,
        "tags": ["客服", "FAQ"],
        "createdAt": "2026-05-05T10:00:00Z",
        "updatedAt": "2026-05-05T10:00:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "pageSize": 20,
    "totalPages": 1
  }
}
```

### 2.2 获取 Agent 详情

`GET /api/v1/agents/{agent_id}`

说明：

- 返回单个 Agent 的完整聚合配置。
- 包含系统提示词、开场白、模型参数、运行参数、工具绑定、知识库绑定和 Workflow 预留引用。

路径参数：

- `agent_id`：Agent ID。

响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "name": "客服助手",
    "description": "回答售前与售后常见问题",
    "avatarUrl": null,
    "status": "active",
    "orchestrationMode": "agent",
    "providerInstanceId": 1,
    "providerModelId": 3,
    "model": {
      "providerInstanceId": 1,
      "providerName": "OpenAI-生产",
      "providerType": "openai",
      "modelId": 3,
      "modelName": "gpt-4.1",
      "displayName": "GPT-4.1"
    },
    "systemPrompt": "你是专业、耐心的客服助手。",
    "openingMessage": "你好，我可以帮你查询产品和订单问题。",
    "modelConfig": {
      "temperature": 0.7,
      "topP": 1,
      "maxTokens": 2048
    },
    "runtimeConfig": {
      "stream": true,
      "maxIterations": 5,
      "memoryWindow": 10
    },
    "workflowRef": null,
    "tools": [
      {
        "toolId": 10,
        "bindingName": "查询订单",
        "isEnabled": true,
        "sortOrder": 0,
        "config": {
          "timeoutSeconds": 20
        },
        "metadata": null
      }
    ],
    "knowledgeBases": [
      {
        "knowledgeBaseId": 20,
        "isEnabled": true,
        "sortOrder": 0,
        "retrievalConfig": {
          "topK": 5,
          "scoreThreshold": 0.5,
          "rerankEnabled": false
        },
        "metadata": null
      }
    ],
    "tags": ["客服", "FAQ"],
    "metadata": null,
    "createdAt": "2026-05-05T10:00:00Z",
    "updatedAt": "2026-05-05T10:00:00Z"
  }
}
```

### 2.3 创建 Agent

`POST /api/v1/agents`

说明：

- 一次性提交 Agent 主体、模型引用、工具绑定和知识库绑定。
- 创建默认状态建议为 `draft`。
- 如果创建时提交 `status = active`，后端必须校验模型配置有效。

请求体结构：

```json
{
  "name": "客服助手",
  "description": "回答售前与售后常见问题",
  "avatarUrl": null,
  "status": "draft",
  "orchestrationMode": "agent",
  "providerInstanceId": 1,
  "providerModelId": 3,
  "systemPrompt": "你是专业、耐心的客服助手。",
  "openingMessage": "你好，我可以帮你查询产品和订单问题。",
  "modelConfig": {
    "temperature": 0.7,
    "topP": 1,
    "maxTokens": 2048
  },
  "runtimeConfig": {
    "stream": true,
    "maxIterations": 5,
    "memoryWindow": 10
  },
  "workflowRef": null,
  "tools": [
    {
      "toolId": 10,
      "bindingName": "查询订单",
      "isEnabled": true,
      "sortOrder": 0,
      "config": {
        "timeoutSeconds": 20
      },
      "metadata": null
    }
  ],
  "knowledgeBases": [
    {
      "knowledgeBaseId": 20,
      "isEnabled": true,
      "sortOrder": 0,
      "retrievalConfig": {
        "topK": 5,
        "scoreThreshold": 0.5,
        "rerankEnabled": false
      },
      "metadata": null
    }
  ],
  "tags": ["客服", "FAQ"],
  "metadata": null
}
```

响应：

- HTTP 状态码：`201`
- `data` 返回 Agent 详情结构。

### 2.4 更新 Agent

`PUT /api/v1/agents/{agent_id}`

说明：

- 请求体结构与创建接口一致。
- 工具绑定和知识库绑定采用整体替换语义。
- 后端更新时对旧绑定执行软删除，再写入新绑定。
- 如果提交 `status = active`，后端必须校验模型配置有效。

路径参数：

- `agent_id`：Agent ID。

响应：

- `data` 返回更新后的 Agent 详情结构。

### 2.5 删除 Agent

`DELETE /api/v1/agents/{agent_id}`

说明：

- 执行软删除。
- 同步软删除 `agent_tool_bindings` 和 `agent_knowledge_bindings`。

响应：

- HTTP 状态码：`204`
- 无响应体。

### 2.6 获取 Agent 配置预览

`GET /api/v1/agents/{agent_id}/config-preview`

说明：

- 返回对前端和排查友好的配置预览。
- 不执行真实 LLM 调用。
- 不执行工具调用。
- 不执行知识库检索。
- 不执行 Workflow。

用途：

- 前端展示“当前 Agent 将如何被 conversation 加载”。
- 帮助管理员检查模型、工具、知识库和运行参数是否按预期解析。

响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "agentId": 1,
    "name": "客服助手",
    "status": "active",
    "orchestrationMode": "agent",
    "isRunnable": true,
    "model": {
      "providerInstanceId": 1,
      "providerModelId": 3,
      "modelName": "gpt-4.1",
      "displayName": "GPT-4.1"
    },
    "enabledToolIds": [10],
    "enabledKnowledgeBaseIds": [20],
    "runtimeConfig": {
      "stream": true,
      "maxIterations": 5,
      "memoryWindow": 10
    },
    "workflowRef": null,
    "warnings": []
  }
}
```

## 3. 数据结构约定

### 3.1 Agent 状态

允许值：

- `draft`
- `active`
- `disabled`
- `archived`

规则：

- `draft` 可保存不完整配置。
- `active` 必须配置有效 `providerModelId`。
- `disabled` 不应被 conversation 运行。
- `archived` 默认不出现在普通筛选结果中，除非显式查询。

### 3.2 编排模式

允许值：

- `agent`
- `chatbot`
- `workflow`

规则：

- 一期默认 `agent`。
- 一期允许保存 `workflow` 草稿，但不允许启用为 `active`，除非未来 Workflow 模块完成。
- 当 `orchestrationMode = workflow` 时，`workflowRef` 是未来扩展字段，当前只透传保存。

### 3.3 模型配置

`modelConfig` 建议字段：

- `temperature`：`0` 到 `2`。
- `topP`：`0` 到 `1`。
- `maxTokens`：大于 `0`。
- `presencePenalty`：可选。
- `frequencyPenalty`：可选。

规则：

- 后端只校验基础数值范围。
- 是否被具体模型支持，由后续 conversation 调用前结合 Provider Model 能力判断。

### 3.4 运行配置

`runtimeConfig` 建议字段：

- `stream`：是否流式输出。
- `maxIterations`：最大工具调用/推理迭代次数。
- `memoryWindow`：保留多少轮上下文。

规则：

- 一期保存并回显。
- conversation 模块后续决定如何使用。

### 3.5 工具绑定

`tools` 数组项字段：

- `toolId`
- `bindingName`
- `isEnabled`
- `sortOrder`
- `config`
- `metadata`

规则：

- 同一个 Agent 下活跃 `toolId` 不可重复。
- `toolId` 必须为正整数。
- `sortOrder` 必须大于等于 `0`。
- 当前数据库不加 `tools.id` 外键，但服务层应校验工具是否存在或在工具模块未完成时标记为暂缓校验。

### 3.6 知识库绑定

`knowledgeBases` 数组项字段：

- `knowledgeBaseId`
- `isEnabled`
- `sortOrder`
- `retrievalConfig`
- `metadata`

`retrievalConfig` 建议字段：

- `topK`
- `scoreThreshold`
- `rerankEnabled`

规则：

- 同一个 Agent 下活跃 `knowledgeBaseId` 不可重复。
- `knowledgeBaseId` 必须为正整数。
- `sortOrder` 必须大于等于 `0`。
- 当前数据库不加 `knowledge_bases.id` 外键，但服务层应校验知识库是否存在或在知识库模块未完成时标记为暂缓校验。

## 4. 错误语义

建议沿用 `AgentErrorCode`：

- `4001 AGENT_NOT_FOUND`：Agent 不存在或已删除。
- `4002 INVALID_CONFIGURATION`：配置不合法。
- `4003 MODEL_NOT_FOUND`：模型不存在或不可用。
- `4004 KNOWLEDGE_BASE_NOT_FOUND`：知识库不存在。
- `4005 TOOL_NOT_FOUND`：工具不存在。

可复用通用错误码：

- `1001 VALIDATION_ERROR`：请求参数校验失败。
- `1003 RESOURCE_ALREADY_EXISTS`：Agent 名称重复。

错误响应统一使用：

```json
{
  "code": 4002,
  "message": "启用 Agent 前必须选择有效模型",
  "data": null
}
```

## 5. 校验规则

基础校验：

- `name` 必填，长度 `1-128`。
- `description` 可选。
- `avatarUrl` 可选，最大 `512`。
- `status` 必须在允许值内。
- `orchestrationMode` 必须在允许值内。
- `providerInstanceId` 可为空。
- `providerModelId` 创建草稿时可为空，启用时必填。
- `systemPrompt` 可为空，但启用时建议非空。
- `tools` 默认为空数组。
- `knowledgeBases` 默认为空数组。
- `tags` 默认为空数组。

业务校验：

- 活跃 Agent 名称不可重复。
- `status = active` 时必须有有效 `providerModelId`。
- `orchestrationMode = workflow` 且 Workflow 模块未完成时，不允许 `status = active`。
- 同一 Agent 下工具 ID 不可重复。
- 同一 Agent 下知识库 ID 不可重复。
- 删除 Agent 时同步软删除绑定关系。

## 6. 兼容性说明

字段命名：

- 后端 ORM 使用 snake_case。
- API 使用 camelCase。
- Pydantic schema 使用 `populate_by_name=True` 和 alias 输出。

兼容策略：

- `workflowRef` 当前允许为 `null` 或普通 JSON 对象。
- 后续 Workflow 模块落地后，可以把 `workflowRef` 收敛为结构化 schema，例如 `workflowDefinitionId` 和 `workflowVersionId`。
- 当前 `config-preview` 不承诺真实运行，只承诺返回配置解析结果。

## 7. 前端聚合接口映射

前端领域模块建议：

- `frontend/src/domain/agent-configuration/types.ts`
- `frontend/src/domain/agent-configuration/api.ts`
- `frontend/src/domain/agent-configuration/service.ts`
- `frontend/src/domain/agent-configuration/queries.ts`
- `frontend/src/domain/agent-configuration/components.tsx`

请求描述符建议：

```ts
export const agentConfigurationApi = {
  listAgents: "GET /agents",
  getAgentDetail: "GET /agents/{agentId}",
  createAgent: "POST /agents",
  updateAgent: "PUT /agents/{agentId}",
  deleteAgent: "DELETE /agents/{agentId}",
  getAgentConfigPreview: "GET /agents/{agentId}/config-preview",
} as const;
```

页面路由建议：

- `/agents`

## 8. 已确认决策

- 一期允许 `orchestrationMode = workflow` 的草稿被创建，但在 Workflow 模块完成前不允许启用。
- 启用 Agent 时 `systemPrompt` 不强制必填，只做前端提示。
- 工具和知识库模块未完成时，服务层暂缓强存在性校验，但保留错误码和接口语义。
