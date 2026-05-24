# 工具集成前端设计

## 1. 页面入口

- 路由：`/tools`
- 导航：运营后台侧栏新增「工具集成」
- 面向用户：平台管理员和 Agent 配置人员

## 2. 页面结构

工具集成页采用现有后台管理页面结构：

- 顶部说明区：说明工具会先在后台完成配置和测试，再交给 Agent 编排侧使用。
- 列表区：复用 `ListTable`，支持关键词、状态、HTTP 方法筛选。
- 聚合表单：复用 `FormDialog`，覆盖工具主体、鉴权、请求模板和参数定义。
- 测试执行弹窗：按工具参数动态生成输入项，调用真实测试接口并展示请求 URL、响应状态和响应预览。
- 执行日志弹窗：展示测试日志、响应状态、耗时和请求地址。
- OpenAPI 导入弹窗：输入 OpenAPI JSON、operation path/method 和 server URL，生成可编辑创建草稿。

## 3. 交互规则

- 新增工具默认 `draft`，避免未测试配置直接进入 Agent 可选列表。
- 编辑密钥时留空表示保留后端已有密钥；页面永不回显明文密钥。
- 删除工具前二次确认；如果工具已被 Agent 绑定，后端返回 `6005`，页面展示后端错误信息。
- OpenAPI 导入只生成草稿，不直接落库；用户仍需检查和提交创建表单。
- 测试执行结果不关闭弹窗，便于用户连续调整参数和复查响应。

## 4. 前端文件

```text
frontend/src/domain/tool-integration/
├── api.ts
├── components.tsx
├── queries.ts
├── service.ts
└── types.ts

frontend/src/pages/tool-integration/ToolIntegrationPage.tsx
```

## 5. 验证记录

- `pnpm lint`：通过。
- `pnpm vitest run src/test/request.test.ts src/test/list-table.test.tsx`：通过，`13 passed`。
- 浏览器冒烟：
  - 登录后访问 `/tools` 成功。
  - 列表接口加载成功。
  - 「新增工具」弹窗打开成功，无 Ant Design 表单警告。
  - 「OpenAPI 导入」使用 Weather API 单 operation 生成草稿成功。
  - 草稿创建工具成功，列表展示新工具。
  - 测试执行弹窗按 `city` 参数发起真实请求并展示响应。
  - 冒烟创建的测试工具已清理。

## 6. 已知限制

- 当前测试执行结果展示响应预览，不提供结构化 JSON 树编辑器。
- OpenAPI 导入一期仅支持单 operation，与后端契约保持一致。
