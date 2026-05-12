# Agent 配置前端文档

## 1. 页面目标

前端提供一个“Agent 配置”页面，用于管理员维护可被对话模块加载的 Agent 配置。

页面路径：

- `/agents`

领域模块：

- `frontend/src/domain/agent-configuration/types.ts`
- `frontend/src/domain/agent-configuration/api.ts`
- `frontend/src/domain/agent-configuration/service.ts`
- `frontend/src/domain/agent-configuration/queries.ts`
- `frontend/src/domain/agent-configuration/components.tsx`

页面组件：

- `frontend/src/pages/agent-configuration/AgentConfigurationPage.tsx`

## 2. 页面职责

页面当前支持：

- 查看 Agent 列表。
- 按关键词、状态、编排模式筛选。
- 新增 Agent。
- 编辑 Agent。
- 删除 Agent。
- 查看配置预览。
- 维护默认 Provider Model ID。
- 维护系统提示词和开场白。
- 维护工具 ID 列表。
- 维护知识库 ID 列表。

## 3. 当前交互结构

### 3.1 列表区

列表字段：

- Agent 名称和描述。
- 状态与编排模式。
- 默认模型。
- 工具数量。
- 知识库数量。
- 最近更新时间。

列表操作：

- 配置预览。
- 编辑。
- 删除。

### 3.2 表单区

当前使用共享 `FormDialog`，字段包括：

- Agent 名称。
- 状态。
- 编排模式。
- Provider 实例 ID。
- Provider Model ID。
- 描述。
- 系统提示词。
- 开场白。
- 工具绑定。
- 知识库绑定。

说明：

- `systemPrompt` 不强制必填。
- Workflow 草稿可以保存。
- Workflow Agent 不允许启用，由后端返回业务错误。
- 工具和知识库当前用 ID 输入，后续模块完成后可替换为选择器。

### 3.3 配置预览

配置预览弹窗展示：

- Agent 名称。
- 状态。
- 编排模式。
- 是否可运行。
- 默认模型。
- 启用工具 ID。
- 启用知识库 ID。
- 配置警告。

## 4. 当前限制

- 没有完整可视化 Workflow 编辑器。
- 没有工具选择器和知识库选择器。
- 没有真实 Agent 试跑按钮。
- 没有浏览器插件点选验证截图，因为 Codex in-app browser 后端未可用。

## 5. 后续迭代建议

后续可增强：

- Provider Model 选择器。
- 工具选择器。
- 知识库选择器。
- 高级模型参数编辑。
- Workflow 草稿入口。
- Agent 对话试跑入口，但应调用 `conversation` 模块。
