# Provider 管理接口文档

## 1. 设计目标

前端只做一个页面，因此接口设计以“聚合视图”优先，而不是暴露多套细碎的子资源接口。

## 2. 接口列表

### 2.1 获取 Provider 列表

`GET /api/v1/llms/providers`

说明：

- 返回分页后的 Provider 摘要列表
- 每项聚合包含基础信息、脱敏鉴权信息、默认模型和健康状态

查询参数：

- `page`
- `pageSize`
- `keyword`
- `providerType`
- `status`

### 2.2 获取 Provider 详情

`GET /api/v1/llms/providers/{provider_id}`

说明：

- 返回单个 Provider 的完整详情
- 包含所有模型配置

### 2.3 创建 Provider

`POST /api/v1/llms/providers`

说明：

- 一次性提交实例信息、鉴权信息和模型数组

请求体结构：

```json
{
  "name": "OpenAI-生产",
  "providerType": "openai",
  "apiFamily": "openai_responses",
  "baseUrl": "https://api.openai.com/v1",
  "status": "active",
  "isDefault": true,
  "priority": 100,
  "notes": "主生产账号",
  "metadata": {},
  "auth": {
    "authType": "api_key",
    "secretValue": "sk-xxxx",
    "headers": null,
    "queryParams": null,
    "metadata": null,
    "expiresAt": null
  },
  "models": [
    {
      "modelName": "gpt-4.1",
      "displayName": "GPT-4.1",
      "status": "active",
      "isDefault": true,
      "sortOrder": 0,
      "supportsChat": true,
      "supportsStream": true,
      "supportsTools": true,
      "supportsStructuredOutput": true,
      "supportsVisionInput": true,
      "supportsAudioInput": false,
      "supportsReasoning": false,
      "supportsEmbeddings": false,
      "contextWindow": 128000,
      "maxOutputTokens": 16384,
      "maxInputTokens": 128000,
      "temperatureSupported": true,
      "topPSupported": true,
      "tags": ["production"],
      "pricing": null,
      "metadata": null
    }
  ]
}
```

### 2.4 更新 Provider

`PUT /api/v1/llms/providers/{provider_id}`

说明：

- 结构与创建接口一致
- 当前模型列表采用整体替换语义
- 若 `auth.secretValue` 为空，则保留原密钥

### 2.5 删除 Provider

`DELETE /api/v1/llms/providers/{provider_id}`

说明：

- 执行软删除
- 子表同步软删除

### 2.6 测试连接

`POST /api/v1/llms/providers/{provider_id}/test-connection`

说明：

- 对当前 Provider 实例执行一次连通性检测
- 后端会把结果回写到 `provider_health_statuses`
- 返回本次检测结果摘要

当前检测策略：

- 以 `base_url` 作为请求目标
- 按当前鉴权配置拼接请求头
- `401/403` 视为鉴权失败
- `2xx` 视为连接成功
- 其他 HTTP 状态视为“已连通但异常”
- 网络错误或超时视为不可达

### 2.7 运行配置预览

`GET /api/v1/llms/providers/{provider_id}/runtime-config`

说明：

- 返回一个脱敏后的 LiteLLM 运行时配置预览
- 可选 `model_name` 查询参数，用于查看指定模型的解析结果
- 不返回明文密钥，只返回掩码值

用途：

- 运维排查配置是否按预期解析
- 前端管理页展示执行层配置预览
- 后续接真实 LiteLLM 调用时作为内部配置解析基础

### 2.8 试跑模型

`POST /api/v1/llms/providers/{provider_id}/invoke-test`

说明：

- 使用当前 Provider 的真实配置发起一次 LiteLLM 调用
- 用于验证“配置管理链路”是否真正能驱动“模型执行链路”
- 成功后会回写当前实例的健康状态
- 失败时会记录最近一次推理错误

请求体结构：

```json
{
  "modelName": "gpt-4.1",
  "prompt": "请用一句话介绍你自己。",
  "temperature": 0.7,
  "maxTokens": 512
}
```

返回结构示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "providerId": 1,
    "modelName": "gpt-4.1",
    "litellmModel": "gpt-4.1",
    "outputText": "你好，我是一个大语言模型助手。",
    "latencyMs": 823
  }
}
```

## 3. 返回结构

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

## 4. 当前校验规则

- Provider 名称不可重复
- 创建时必须提供密钥
- 同一 Provider 至少有一个模型
- 同一 Provider 模型名不可重复
- 同一 Provider 只能有一个默认模型
- 如果未显式指定默认模型，后端会将第一条模型自动设为默认

## 5. 错误语义

当前主要错误语义：

- Provider 不存在
- Provider 名称已存在
- 模型数组为空
- 同实例模型重复
- 默认模型冲突
- 参数校验失败
- 未配置鉴权信息
- 测试连接失败
- LiteLLM 调用失败
