# Provider 管理前端文档

## 1. 页面目标

前端只做一个“模型提供商管理”页面，不拆成两个独立页面。

页面既要满足一期易用性，也要兼容后端的多模型扩展能力。

## 2. 页面职责

页面职责：

- 查看 Provider 列表
- 新增 Provider
- 编辑 Provider
- 删除 Provider
- 在同一编辑面板中维护模型列表

## 3. 页面建议结构

建议分为三个视觉区块：

### 3.1 列表区

展示摘要字段：

- 名称
- 提供商类型
- 协议类型
- 默认模型
- 健康状态
- 启用状态

### 3.2 编辑区

可使用抽屉或内嵌编辑面板，维护：

- 基础信息
- 鉴权信息
- 模型列表

### 3.3 模型子编辑区

在同一页面中支持：

- 新增模型
- 编辑模型
- 删除模型
- 设置默认模型

## 4. 当前实现

当前前端已落地为单一路由页面：

- 路由：`/providers`
- 页面组件：`frontend/src/pages/provider-management/ProviderManagementPage.tsx`

当前领域模块：

- `frontend/src/domain/provider-management/api.ts`
- `frontend/src/domain/provider-management/service.ts`
- `frontend/src/domain/provider-management/queries.ts`
- `frontend/src/domain/provider-management/types.ts`
- `frontend/src/domain/provider-management/components.tsx`

当前页面交互：

- 列表区展示 Provider 摘要
- 支持按关键词、提供商类型、实例状态筛选
- 支持查看健康状态详情浮层
- 支持查看运行配置预览弹窗
- 支持“试跑模型”弹窗，直接验证真实调用链路
- 点击“新增提供商”打开聚合表单
- 点击“编辑”拉取详情并回填
- 点击“删除”执行软删除
- 点击“测试连接”触发后端连通性检测
- 模型列表在同一表单中内嵌编辑
- 提供商类型变更时自动推荐协议族、鉴权方式和默认地址

## 5. 表单结构

当前单页表单包含三组信息：

### 5.1 基础信息

- 提供商名称
- 提供商类型
- 协议族
- Base URL
- 地址提示
- 实例状态
- 优先级
- 是否默认实例
- 备注

### 5.2 鉴权信息

- 鉴权方式
- 鉴权提示
- 密钥

说明：

- 编辑时密钥默认不回填明文
- 留空表示保持原密钥不变

### 5.3 模型列表

每个模型卡片当前支持：

- 模型名称
- 展示名称
- 备注
- 状态
- 是否默认模型
- 上下文窗口
- 最大输入 Token
- 最大输出 Token
- 能力开关

## 6. 前后端交互模型

前端聚合维护：

- 一个 Provider 表单
- 一个 Auth 表单
- 一个 Models 数组表单

提交时一次性调用：

- `POST /api/v1/llms/providers`
- `PUT /api/v1/llms/providers/{provider_id}`

读取时使用：

- 列表：`GET /api/v1/llms/providers`
- 详情：`GET /api/v1/llms/providers/{provider_id}`
- 删除：`DELETE /api/v1/llms/providers/{provider_id}`
- 试跑：`POST /api/v1/llms/providers/{provider_id}/invoke-test`

## 7. 试跑模型交互

当前实现中，列表操作区提供“试跑模型”入口。

交互过程：

- 先拉取 Provider 详情，得到当前可用模型列表
- 弹出试跑表单，选择模型并输入测试提示词
- 调用后端真实 LiteLLM 执行接口
- 在同一弹窗内展示模型名、LiteLLM 模型串、耗时和输出文本
- 成功或失败后都刷新列表，以同步健康状态

## 8. 当前待补内容

后续仍需继续补充：

- 更细粒度的模型参数编辑
- 前端 E2E 或更完整的交互测试
