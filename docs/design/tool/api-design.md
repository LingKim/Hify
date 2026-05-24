# 工具集成接口文档

## 1. 设计目标

工具接口服务三个核心场景：

- 工具管理页：列表、详情、创建、编辑、删除、测试执行。
- Agent 配置页：选择已启用工具，不再手填工具 ID。
- OpenAPI 导入：从一个 OpenAPI operation 生成工具草稿，再由创建接口落库。

一期工具是可管理的 HTTP operation。`tool` 模块负责工具定义、鉴权密文、参数 schema 和单次 HTTP 执行；`conversation` 模块后续负责决定何时调用工具以及如何把结果回喂 LLM。

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
- 用户表单不暴露内部 ID 输入；引用工具时使用选项接口。
- 所有鉴权 secret 只允许写入，不允许明文读出。

## 3. 公共对象

### 3.1 工具状态

`status` 可选值：

- `draft`：草稿，可编辑，不允许被新绑定启用。
- `enabled`：启用，可被 Agent 绑定和测试执行。
- `disabled`：停用，保留配置，不允许被 Agent 运行。
- `archived`：归档，默认列表不展示，不允许执行。

### 3.2 鉴权对象

写入结构：

```json
{
  "authType": "bearer",
  "secretValue": "token-value",
  "headerName": "Authorization",
  "queryName": null
}
```

读取结构：

```json
{
  "authType": "bearer",
  "secretMasked": "tok...alue",
  "headerName": "Authorization",
  "queryName": null,
  "lastRotatedAt": "2026-05-23T08:00:00Z"
}
```

规则：

- `authType` 可选 `none`、`bearer`、`api_key_header`、`api_key_query`。
- `authType = none` 时 `secretValue` 可为空。
- 更新时如果 `secretValue` 为空或未提交，保留原密钥。
- 接口响应永不返回 `secretValue` 和密文。

### 3.3 参数对象

```json
{
  "name": "city",
  "label": "城市",
  "description": "要查询天气的城市名称",
  "paramLocation": "query",
  "schemaType": "string",
  "isRequired": true,
  "defaultValue": null,
  "enumValues": null,
  "schema": {
    "type": "string"
  },
  "sortOrder": 0,
  "metadata": null
}
```

规则：

- `paramLocation` 可选 `path`、`query`、`header`、`body`。
- `schemaType` 可选 `string`、`number`、`integer`、`boolean`、`object`、`array`。
- 同一工具下活跃参数 `(name, paramLocation)` 不可重复。
- `header` 参数不用于保存密钥；密钥统一走鉴权对象。

### 3.4 工具详情对象

```json
{
  "id": 1,
  "name": "查询天气",
  "description": "按城市查询天气",
  "status": "enabled",
  "toolType": "http",
  "sourceType": "manual",
  "httpMethod": "GET",
  "url": "https://api.example.com/weather",
  "timeoutSeconds": 15,
  "headersTemplate": {
    "Accept": "application/json"
  },
  "queryTemplate": {
    "city": "{{city}}"
  },
  "bodyTemplate": null,
  "contentType": "application/json",
  "auth": {
    "authType": "api_key_header",
    "secretMasked": "sk-...1234",
    "headerName": "X-API-Key",
    "queryName": null,
    "lastRotatedAt": "2026-05-23T08:00:00Z"
  },
  "parameters": [
    {
      "name": "city",
      "label": "城市",
      "description": "要查询天气的城市名称",
      "paramLocation": "query",
      "schemaType": "string",
      "isRequired": true,
      "defaultValue": null,
      "enumValues": null,
      "schema": {
        "type": "string"
      },
      "sortOrder": 0,
      "metadata": null
    }
  ],
  "openapiSource": null,
  "lastTestStatus": "success",
  "lastTestAt": "2026-05-23T08:30:00Z",
  "lastTestLatencyMs": 245,
  "lastErrorMessage": null,
  "metadata": null,
  "createdAt": "2026-05-23T08:00:00Z",
  "updatedAt": "2026-05-23T08:30:00Z"
}
```

## 4. 接口列表

### 4.1 获取工具列表

`GET /api/v1/tools`

说明：

- 返回分页后的工具摘要列表。
- 默认不返回完整参数 schema 和鉴权写入信息。
- 默认排除 `archived` 和软删除记录。

查询参数：

- `page`：默认 `1`。
- `pageSize`：默认 `20`，最大 `100`。
- `keyword`：按名称、描述、URL 搜索。
- `status`：`draft`、`enabled`、`disabled`、`archived`。
- `sourceType`：`manual`、`openapi`。
- `httpMethod`：`GET`、`POST`、`PUT`、`PATCH`、`DELETE`。

响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "name": "查询天气",
        "description": "按城市查询天气",
        "status": "enabled",
        "toolType": "http",
        "sourceType": "manual",
        "httpMethod": "GET",
        "url": "https://api.example.com/weather",
        "authType": "api_key_header",
        "parameterCount": 1,
        "boundAgentCount": 2,
        "lastTestStatus": "success",
        "lastTestAt": "2026-05-23T08:30:00Z",
        "lastTestLatencyMs": 245,
        "createdAt": "2026-05-23T08:00:00Z",
        "updatedAt": "2026-05-23T08:30:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "pageSize": 20,
    "totalPages": 1
  }
}
```

### 4.2 获取工具选项

`GET /api/v1/tools/options`

说明：

- 给 Agent 配置页工具选择器使用。
- 默认只返回 `enabled` 且未删除的工具。

查询参数：

- `keyword`。
- `status`：默认 `enabled`。

响应示例：

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

### 4.3 获取工具详情

`GET /api/v1/tools/{tool_id}`

说明：

- 返回单个工具完整聚合详情。
- 包含脱敏鉴权、参数定义、OpenAPI 来源摘要和最近测试状态。

路径参数：

- `tool_id`：工具 ID。

响应：

- `data` 返回工具详情对象。

### 4.4 创建工具

`POST /api/v1/tools`

说明：

- 一次性提交工具主体、鉴权配置和参数数组。
- 用于手工创建，也用于 OpenAPI 草稿确认后的落库。

请求体：

```json
{
  "name": "查询天气",
  "description": "按城市查询天气",
  "status": "draft",
  "sourceType": "manual",
  "httpMethod": "GET",
  "url": "https://api.example.com/weather",
  "timeoutSeconds": 15,
  "headersTemplate": {
    "Accept": "application/json"
  },
  "queryTemplate": {
    "city": "{{city}}"
  },
  "bodyTemplate": null,
  "contentType": "application/json",
  "auth": {
    "authType": "api_key_header",
    "secretValue": "sk-test",
    "headerName": "X-API-Key",
    "queryName": null
  },
  "parameters": [
    {
      "name": "city",
      "label": "城市",
      "description": "要查询天气的城市名称",
      "paramLocation": "query",
      "schemaType": "string",
      "isRequired": true,
      "defaultValue": null,
      "enumValues": null,
      "schema": {
        "type": "string"
      },
      "sortOrder": 0,
      "metadata": null
    }
  ],
  "openapiSource": null,
  "metadata": null
}
```

规则：

- `name` 必填，当前用户未删除工具中不可重名。
- `sourceType` 默认 `manual`。
- `toolType` 不由前端提交，一期后端固定为 `http`。
- `url` 必须是合法 `http` / `https` URL。
- 默认禁止访问明显危险地址段；本地开发如需放开，由后端配置控制。
- `timeoutSeconds` 范围为 `1` 到 `60`。
- `status = enabled` 时必须具备合法 URL、HTTP 方法、鉴权配置和参数定义。
- `parameters` 中同一 `name + paramLocation` 不可重复。

响应：

- HTTP 状态码：`201`。
- `data` 返回工具详情对象。

### 4.5 更新工具

`PUT /api/v1/tools/{tool_id}`

说明：

- 请求体结构与创建接口一致。
- 参数数组采用整体替换语义。
- 鉴权对象采用整体更新语义，但 `secretValue` 为空或未提交时保留原密钥。
- 更新工具不会自动修改已有 Agent 绑定配置。

路径参数：

- `tool_id`：工具 ID。

响应：

- `data` 返回更新后的工具详情对象。

### 4.6 删除工具

`DELETE /api/v1/tools/{tool_id}`

说明：

- 执行软删除。
- 同步软删除鉴权配置和参数定义。
- 执行日志默认保留。
- 如果工具存在活跃 Agent 绑定，返回业务错误，要求先解绑。

响应：

- 成功：`204 No Content`。
- 被绑定阻止删除：

```json
{
  "code": 6005,
  "message": "工具已被 Agent 绑定，请先解绑后再删除",
  "data": null
}
```

### 4.7 测试执行工具

`POST /api/v1/tools/{tool_id}/execute-test`

说明：

- 使用当前工具配置和测试参数真实发起一次 HTTP 请求。
- 写入 `tool_execution_logs`。
- 回写工具最近测试状态。
- 用于后台验证工具链路，不代表 Agent 自动调用闭环完成。

路径参数：

- `tool_id`：工具 ID。

请求体：

```json
{
  "parameters": {
    "city": "杭州"
  },
  "timeoutSeconds": 10
}
```

规则：

- 只能测试 `enabled` 或 `draft` 工具；`disabled`、`archived` 不允许执行。
- 必填参数缺失时不发起外部请求，直接返回校验错误。
- `timeoutSeconds` 可覆盖工具默认值，但仍不能超过 `60`。
- 请求和响应日志必须脱敏、截断。

成功响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "logId": 100,
    "toolId": 1,
    "status": "success",
    "request": {
      "method": "GET",
      "url": "https://api.example.com/weather?city=杭州",
      "headers": {
        "Accept": "application/json",
        "X-API-Key": "sk-...test"
      },
      "bodyPreview": null
    },
    "response": {
      "statusCode": 200,
      "headers": {
        "content-type": "application/json"
      },
      "bodyPreview": "{\"city\":\"杭州\",\"weather\":\"晴\"}"
    },
    "latencyMs": 245,
    "errorCode": null,
    "errorMessage": null,
    "createdAt": "2026-05-23T08:30:00Z"
  }
}
```

失败响应说明：

- 外部接口返回 4xx/5xx 时，HTTP 状态仍返回 `200`，`data.status = failed`，表示工具测试流程本身完成但上游业务失败。
- 请求构造失败、URL 被安全策略拦截、参数校验失败时，返回业务错误。
- 网络错误或超时返回业务错误，并写入失败日志。

### 4.8 获取工具执行日志

`GET /api/v1/tools/{tool_id}/execution-logs`

说明：

- 返回某个工具的测试和执行日志。
- 一期主要用于测试执行结果抽屉；后续可支持会话工具调用排查。

查询参数：

- `page`：默认 `1`。
- `pageSize`：默认 `20`，最大 `100`。
- `source`：`test`、`conversation`。
- `status`：`success`、`failed`、`timeout`。

响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 100,
        "toolId": 1,
        "source": "test",
        "status": "success",
        "requestMethod": "GET",
        "requestUrl": "https://api.example.com/weather?city=杭州",
        "responseStatusCode": 200,
        "latencyMs": 245,
        "errorCode": null,
        "errorMessage": null,
        "createdAt": "2026-05-23T08:30:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "pageSize": 20,
    "totalPages": 1
  }
}
```

### 4.9 OpenAPI operation 导入预览

`POST /api/v1/tools/import-openapi/preview`

说明：

- 解析一个 OpenAPI 3.x 文档中的单个 operation。
- 返回可编辑的工具创建草稿，不直接落库。
- 一期只支持单 operation 导入，避免一次导入多个工具导致确认成本过高。

请求体：

```json
{
  "document": {
    "openapi": "3.0.3",
    "info": {
      "title": "Weather API",
      "version": "1.0.0"
    },
    "servers": [
      {
        "url": "https://api.example.com"
      }
    ],
    "paths": {
      "/weather": {
        "get": {
          "operationId": "getWeather",
          "summary": "查询天气",
          "parameters": [
            {
              "name": "city",
              "in": "query",
              "required": true,
              "schema": {
                "type": "string"
              }
            }
          ]
        }
      }
    }
  },
  "operation": {
    "path": "/weather",
    "method": "GET"
  },
  "serverUrl": "https://api.example.com"
}
```

响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "draft": {
      "name": "查询天气",
      "description": "查询天气",
      "status": "draft",
      "sourceType": "openapi",
      "httpMethod": "GET",
      "url": "https://api.example.com/weather",
      "timeoutSeconds": 15,
      "headersTemplate": {
        "Accept": "application/json"
      },
      "queryTemplate": {
        "city": "{{city}}"
      },
      "bodyTemplate": null,
      "contentType": "application/json",
      "auth": {
        "authType": "none",
        "secretValue": null,
        "headerName": null,
        "queryName": null
      },
      "parameters": [
        {
          "name": "city",
          "label": "city",
          "description": "",
          "paramLocation": "query",
          "schemaType": "string",
          "isRequired": true,
          "defaultValue": null,
          "enumValues": null,
          "schema": {
            "type": "string"
          },
          "sortOrder": 0,
          "metadata": null
        }
      ],
      "openapiSource": {
        "title": "Weather API",
        "version": "1.0.0",
        "operationId": "getWeather",
        "path": "/weather",
        "method": "GET",
        "serverUrl": "https://api.example.com"
      },
      "metadata": null
    },
    "warnings": []
  }
}
```

规则：

- 只支持 OpenAPI 3.x。
- `operation.path` 和 `operation.method` 必须能在文档中找到。
- 如果 schema 过于复杂，尽量保留在 `schema` 字段并返回 warning。
- 不自动导入安全方案密钥，只生成 `authType` 草稿，密钥由用户确认时填写。

## 5. 错误码

沿用已有 `ToolErrorCode` 并补充：

- `6001 TOOL_NOT_FOUND`：工具不存在或已删除。
- `6002 INVALID_OPENAPI_SCHEMA`：OpenAPI 文档不合法或 operation 不存在。
- `6003 TOOL_EXECUTION_FAILED`：工具执行失败。
- `6004 TOOL_EXECUTION_TIMEOUT`：工具执行超时。
- `6005 TOOL_IN_USE`：工具已被 Agent 绑定，不能删除。
- `6006 INVALID_TOOL_CONFIGURATION`：工具配置不合法。
- `6007 TOOL_SECURITY_BLOCKED`：目标 URL 被安全策略拦截。

可复用通用错误码：

- `1001 VALIDATION_ERROR`：请求参数校验失败。
- `1002 RESOURCE_NOT_FOUND`：资源不存在。
- `1003 RESOURCE_ALREADY_EXISTS`：工具名称重复。
- `1005 UNAUTHORIZED`：未登录。
- `1006 FORBIDDEN`：无权限。

错误响应统一使用：

```json
{
  "code": 6006,
  "message": "启用工具前必须配置合法 URL 和请求方法",
  "data": null
}
```

## 6. 校验规则

### 6.1 工具配置校验

- `name` 长度为 `1` 到 `128`。
- `description` 可空。
- `url` 长度不超过 `2048`。
- `httpMethod` 必须为支持枚举。
- `timeoutSeconds` 范围 `1` 到 `60`。
- `headersTemplate`、`queryTemplate`、`bodyTemplate` 必须是 JSON object 或 `null`。
- `contentType` 默认 `application/json`。
- `status = enabled` 时必须通过 URL、安全策略、方法和鉴权配置校验。

### 6.2 URL 安全校验

- 只允许 `http` / `https`。
- 默认禁止 `localhost`、`127.0.0.0/8`、`::1`、link-local、metadata service 地址。
- 重定向后的最终地址也必须经过安全校验。
- 本地开发若确需内网地址，应通过后端配置显式放开。

### 6.3 Secret 校验

- `authType = bearer` 时，默认使用 `Authorization: Bearer <secret>`。
- `authType = api_key_header` 时，`headerName` 必填。
- `authType = api_key_query` 时，`queryName` 必填。
- `secretValue` 写入后必须加密存储。
- 响应和日志中必须脱敏。

### 6.4 参数校验

- `name` 必须是非空字符串。
- `paramLocation` 必须为支持枚举。
- `schemaType` 必须为支持枚举。
- 必填参数在测试执行时必须提供。
- path 参数必须能在 URL 模板中找到对应占位符。

## 7. 分页、排序和搜索

一期列表接口支持：

- 按 `updatedAt desc` 默认排序。
- `keyword` 搜索 `name`、`description`、`url`。
- 状态、来源、HTTP 方法筛选。

暂不提供复杂排序参数。后续如需要，可增加：

- `sortBy`：`updatedAt`、`createdAt`、`name`、`lastTestAt`。
- `sortOrder`：`asc`、`desc`。

## 8. 前端联调约定

- 工具管理页通过 `GET /api/v1/tools` 初始化列表。
- 创建和编辑使用同一份聚合表单模型。
- 测试执行弹窗使用详情接口中的 `parameters` 动态生成输入项。
- Agent 配置页工具选择器调用 `GET /api/v1/tools/options`。
- OpenAPI 导入先调用预览接口，用户确认或编辑草稿后再调用创建接口。
- 删除前端需要二次确认；如果后端返回 `6005`，弹窗提示用户先到 Agent 配置中解绑。

## 9. 后端 curl 验证清单

后端接口开发完成后，必须按下面顺序用真实 `curl` 跑通，再进入前端真实联调：

1. 登录获取 token。
2. `POST /api/v1/tools` 创建无鉴权 GET 工具。
3. `GET /api/v1/tools` 验证列表。
4. `GET /api/v1/tools/options` 验证选项。
5. `GET /api/v1/tools/{tool_id}` 验证详情。
6. `PUT /api/v1/tools/{tool_id}` 验证更新和密钥保留语义。
7. `POST /api/v1/tools/{tool_id}/execute-test` 验证真实 HTTP 执行。
8. `GET /api/v1/tools/{tool_id}/execution-logs` 验证日志。
9. `POST /api/v1/tools/import-openapi/preview` 验证 OpenAPI 草稿生成。
10. `DELETE /api/v1/tools/{tool_id}` 验证软删除。
11. 创建 Agent 绑定工具后再次删除工具，验证 `6005 TOOL_IN_USE`。

每条 curl 都需要确认：

- HTTP 状态码符合契约。
- 响应 envelope 使用 `code/message/data`。
- Secret 没有明文返回。
- 后端日志无 traceback。
