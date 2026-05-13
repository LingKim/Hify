# 知识库 / RAG 接口文档

## 1. 设计目标

知识库接口服务两个核心场景：

- 知识库工作台：列表、详情、文档流、上传、检索测试、绑定 Agent 摘要。
- 会话运行：Conversation 根据 Agent 绑定知识库执行检索，并把命中片段注入 LLM。

前端主页面不做传统 Table，因此接口优先提供聚合视图，减少页面拼装成本。

所有接口统一使用：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

列表接口的 `data` 使用分页结构：

```json
{
  "list": [],
  "total": 0,
  "page": 1,
  "pageSize": 20,
  "totalPages": 0
}
```

## 2. 字段命名约定

- 后端 Python/数据库使用 snake_case。
- HTTP JSON 使用 camelCase。
- 业务状态值使用小写英文枚举。
- 所有用户可见的外键字段都通过选项接口选择，不要求用户手填 ID。

## 3. 接口列表

### 3.1 获取知识库列表

`GET /api/v1/knowledge-bases`

说明：

- 返回当前用户可见的知识库卡片列表。
- 用于左侧知识空间和页面初始数据。

查询参数：

- `page`：默认 `1`。
- `pageSize`：默认 `20`。
- `keyword`：按知识库名称、描述搜索。
- `status`：`draft`、`enabled`、`archived`。
- `visibility`：`private`、`workspace`。

响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "name": "产品资料库",
        "description": "产品说明、版本记录与 FAQ",
        "status": "enabled",
        "visibility": "workspace",
        "documentCount": 24,
        "chunkCount": 1286,
        "lastIndexedAt": "2026-05-13T06:20:00Z",
        "createdAt": "2026-05-13T04:00:00Z",
        "updatedAt": "2026-05-13T06:20:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "pageSize": 20,
    "totalPages": 1
  }
}
```

### 3.2 获取知识库工作台详情

`GET /api/v1/knowledge-bases/{knowledge_base_id}`

说明：

- 返回右侧工作台需要的聚合详情。
- 包含知识库配置、统计信息、最近文档、绑定 Agent 摘要。

响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "name": "产品资料库",
    "description": "产品说明、版本记录与 FAQ",
    "status": "enabled",
    "visibility": "workspace",
    "embeddingModel": "Qwen/Qwen3-Embedding-8B",
    "embeddingDimensions": 1024,
    "chunkSize": 800,
    "chunkOverlap": 120,
    "defaultTopK": 5,
    "defaultScoreThreshold": 0.65,
    "documentCount": 24,
    "chunkCount": 1286,
    "processingDocumentCount": 2,
    "failedDocumentCount": 1,
    "health": {
      "score": 78,
      "label": "健康",
      "suggestion": "建议补充供应商配置相关文档"
    },
    "boundAgents": [
      {
        "agentId": 12,
        "agentName": "售前助手",
        "isEnabled": true,
        "topK": 5,
        "scoreThreshold": 0.65
      }
    ],
    "createdAt": "2026-05-13T04:00:00Z",
    "updatedAt": "2026-05-13T06:20:00Z"
  }
}
```

### 3.3 创建知识库

`POST /api/v1/knowledge-bases`

请求体：

```json
{
  "name": "产品资料库",
  "description": "产品说明、版本记录与 FAQ",
  "status": "draft",
  "visibility": "private",
  "chunkSize": 800,
  "chunkOverlap": 120,
  "defaultTopK": 5,
  "defaultScoreThreshold": 0.65,
  "metadata": {}
}
```

规则：

- `name` 必填，当前用户可见范围内不能和未删除知识库重名。
- `status` 默认 `draft`。
- `visibility` 默认 `private`。
- `chunkOverlap` 必须小于 `chunkSize`。
- Embedding 模型和维度从后端环境配置读取，不由前端提交。

响应：

- 返回知识库详情结构。

### 3.4 更新知识库

`PATCH /api/v1/knowledge-bases/{knowledge_base_id}`

请求体：

```json
{
  "name": "产品资料库",
  "description": "产品说明、版本记录与 FAQ",
  "status": "enabled",
  "visibility": "workspace",
  "chunkSize": 800,
  "chunkOverlap": 120,
  "defaultTopK": 5,
  "defaultScoreThreshold": 0.65,
  "metadata": {}
}
```

规则：

- 已有文档不会因为修改 `chunkSize` 或 `chunkOverlap` 自动重建索引。
- 新上传或手动重建的文档使用新的切片参数。
- `archived` 知识库不参与会话检索。

响应：

- 返回知识库详情结构。

### 3.5 删除知识库

`DELETE /api/v1/knowledge-bases/{knowledge_base_id}`

说明：

- 执行软删除。
- 同步软删除文档和切片。
- Agent 绑定关系同步软删除或禁用，避免会话继续检索。

响应：

- `204 No Content`。

### 3.6 获取知识库选项

`GET /api/v1/knowledge-bases/options`

说明：

- 给 Agent 配置页选择知识库使用。
- 只返回当前用户可见且可绑定的知识库。

查询参数：

- `keyword`
- `status`：默认 `enabled`。

响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "产品资料库",
      "status": "enabled",
      "documentCount": 24,
      "chunkCount": 1286
    }
  ]
}
```

### 3.7 上传文档

`POST /api/v1/knowledge-bases/{knowledge_base_id}/documents`

请求类型：

- `multipart/form-data`

字段：

- `file`：必填。
- `metadata`：可选 JSON 字符串。

规则：

- 支持 `.txt`、`.md`、`.pdf`、`.docx`。
- 单文件大小默认不超过 20 MB。
- 知识库为 `archived` 时不可上传。
- 上传成功后先创建文档记录，再触发处理流程。

响应示例：

```json
{
  "code": 201,
  "message": "success",
  "data": {
    "id": 101,
    "knowledgeBaseId": 1,
    "filename": "Hify 产品使用手册.pdf",
    "fileExt": ".pdf",
    "mimeType": "application/pdf",
    "fileSizeBytes": 204800,
    "status": "uploaded",
    "processStage": "uploaded",
    "chunkCount": 0,
    "tokenCount": 0,
    "errorCode": null,
    "errorMessage": null,
    "createdAt": "2026-05-13T06:20:00Z",
    "updatedAt": "2026-05-13T06:20:00Z"
  }
}
```

### 3.8 获取文档列表

`GET /api/v1/knowledge-bases/{knowledge_base_id}/documents`

查询参数：

- `page`
- `pageSize`
- `keyword`
- `status`：`uploaded`、`processing`、`completed`、`failed`、`disabled`。

响应：

- 返回分页后的文档摘要。

### 3.9 获取文档详情

`GET /api/v1/knowledge-bases/{knowledge_base_id}/documents/{document_id}`

说明：

- 返回单个文档详情。
- 可用于失败原因抽屉或详情查看。

### 3.10 删除文档

`DELETE /api/v1/knowledge-bases/{knowledge_base_id}/documents/{document_id}`

说明：

- 执行软删除。
- 同步软删除该文档下的 chunks。
- 更新知识库 `documentCount` 和 `chunkCount`。

响应：

- `204 No Content`。

### 3.11 重新处理文档

`POST /api/v1/knowledge-bases/{knowledge_base_id}/documents/{document_id}/reprocess`

说明：

- 对失败或已完成文档重新执行文本抽取、切片和向量化。
- 旧 chunks 软删除，新 chunks 重新写入。

响应：

- 返回文档详情。

### 3.12 检索测试

`POST /api/v1/knowledge-bases/{knowledge_base_id}/retrieval-test`

请求体：

```json
{
  "query": "如何配置模型供应商？",
  "topK": 5,
  "scoreThreshold": 0.65
}
```

规则：

- `query` 必填。
- `topK` 为空时使用知识库默认值。
- `scoreThreshold` 为空时使用知识库默认值。
- 只检索 `completed` 文档下未删除 chunks。
- 本接口会写入 `knowledge_retrieval_logs`，`source = test`。

响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "query": "如何配置模型供应商？",
    "topK": 5,
    "scoreThreshold": 0.65,
    "latencyMs": 42,
    "hits": [
      {
        "chunkId": 9001,
        "documentId": 101,
        "documentName": "Hify 产品使用手册.pdf",
        "content": "管理员进入模型供应商管理页，创建 Provider...",
        "score": 0.86,
        "pageNumber": 3,
        "sectionTitle": "模型供应商配置"
      }
    ]
  }
}
```

## 4. 会话内部检索接口

Conversation 不通过 HTTP 调用 Knowledge，而是在 service 层调用：

```python
await KnowledgeService(db).retrieve_for_conversation(
    knowledge_base_ids=[1, 2],
    query="如何配置模型供应商？",
    user_id=current_user.id,
    conversation_id=conversation.id,
    run_id=run.id,
    retrieval_configs={1: {"topK": 5, "scoreThreshold": 0.65}},
)
```

返回内部结构：

```json
{
  "hits": [
    {
      "knowledgeBaseId": 1,
      "chunkId": 9001,
      "documentId": 101,
      "documentName": "Hify 产品使用手册.pdf",
      "content": "管理员进入模型供应商管理页...",
      "score": 0.86,
      "pageNumber": 3,
      "sectionTitle": "模型供应商配置"
    }
  ],
  "contextText": "【产品资料库 / Hify 产品使用手册.pdf / 第 3 页】..."
}
```

Conversation 注入规则：

- 如果 Agent 没有启用知识库绑定，不执行检索。
- 如果检索无命中，不阻断正常会话。
- 如果检索失败，记录 run metadata，并继续走普通 LLM 会话或返回可重试错误。
- 注入内容放在系统提示词之后、历史消息之前，作为“参考资料”消息。

## 5. 错误语义

主要错误：

- 知识库不存在。
- 知识库名称重复。
- 知识库状态不允许当前操作。
- 文档不存在。
- 文件格式不支持。
- 文件大小超过限制。
- 文档处理失败。
- 文档仍在处理中，不能执行某些操作。
- Embedding 配置缺失。
- 向量检索失败。

错误响应仍走统一异常结构，由项目全局异常处理转换为：

```json
{
  "code": 5003,
  "message": "不支持的文档格式",
  "data": null
}
```

## 6. 前端聚合需求

知识库工作台首屏建议调用：

1. `GET /api/v1/knowledge-bases`
2. `GET /api/v1/knowledge-bases/{id}`
3. `GET /api/v1/knowledge-bases/{id}/documents`

切换左侧知识库时，只刷新第 2 和第 3 个请求。

上传文档成功后：

- 立即把文档插入文档流。
- 轮询文档列表或详情，直到状态变为 `completed` 或 `failed`。

检索测试成功后：

- 直接渲染 `hits`。
- 无命中时展示空状态，不视为接口失败。
