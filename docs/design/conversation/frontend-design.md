# 会话模块前端设计

## 1. 页面拆分结论

会话模块前端拆成两个一级菜单：

- `对话使用`：路由 `/chat`
- `会话日志`：路由 `/conversations`

拆分原因：

- `对话使用` 是高频实时工作台，核心是低干扰输入、流式反馈和快速继续上下文。
- `会话日志` 是管理和排查页面，核心是检索、筛选、查看明细、归档和删除。
- 两者共享同一套 conversation domain API，但页面状态和交互目标不同，不应塞进
  一个页面。

## 2. 菜单与路由

新增侧边栏菜单：

- `对话使用`
  - icon 建议使用消息或评论类图标。
  - path: `/chat`
  - tab title: `对话使用`
- `会话日志`
  - icon 建议使用列表或历史类图标。
  - path: `/conversations`
  - tab title: `会话日志`

保留已有菜单：

- 首页
- 模型提供商
- Agent 配置
- 联调预览
- 公共组件

## 3. 前端领域结构

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

命名说明：

- 领域仍叫 `conversation`，对应后端模块。
- 使用页面叫 `chat`，避免用户菜单里出现偏技术的“conversation”。
- 管理页面叫 `ConversationLogPage`，强调日志和排查，不与聊天工作台混淆。

## 4. `对话使用` 页面设计

### 4.1 页面目标

`/chat` 面向真实使用者，用于和 Agent 流式对话。

登录功能完成前，页面默认使用系统 root 用户上下文；前端不展示用户切换，也不让
用户选择 owner。

页面必须支持：

- 选择 Agent。
- 新建会话。
- 查看、搜索、分页切换当前用户的会话。
- 展示消息流。
- 发送消息并展示 SSE 增量输出。
- 断流、鉴权失败、限流、超时等错误提示。
- 刷新后恢复当前会话消息历史。

页面不承载：

- 高级筛选。
- 批量操作。
- 软删除确认流。
- 运行日志深度排查。

### 4.2 桌面布局

采用三段式工作台：

```text
┌──────────────────────────────────────────────────────────────┐
│ 顶部栏：Agent 选择 / 当前会话标题 / 运行状态 / 新建会话        │
├───────────────┬──────────────────────────────────────────────┤
│ 会话列表       │ 消息流区域                                    │
│ 搜索框         │ - opening message / empty state                │
│ 会话项 + 删除  │ - user bubble                                  │
│ 分页           │ - assistant streaming bubble                   │
│               │                                                │
│               ├──────────────────────────────────────────────┤
│               │ 输入区：textarea / 发送 / 停止或重试            │
└───────────────┴──────────────────────────────────────────────┘
```

区域职责：

- 顶部栏：控制当前运行上下文，避免把 Agent 选择藏在侧边栏深处。
- 会话列表栏：支持关键词模糊搜索、分页、点击切换和归档，不做复杂筛选。
- 消息流：承载对话内容和 SSE 状态。
- 输入区：固定在主区域底部，发送中禁用重复提交。

推荐宽度：

- 会话列表栏：280px。
- 主对话区：自适应。
- 页面整体占满 `app-content`，减少卡片包裹感。

### 4.3 会话列表栏

功能：

- 顶部提供搜索框，按标题和最后消息摘要模糊搜索。
- 展示当前用户 active 会话，默认不显示 archived。
- 支持分页，默认每页 20 条。
- 每项展示标题、Agent 名称、最后消息摘要、最后消息时间。
- 当前会话高亮。
- 每项右侧提供删除 icon；在 `/chat` 中删除的含义是归档会话。
- 顶部提供“新建会话”按钮。

不做：

- Agent、状态、时间范围等高级筛选。
- 批量删除。
- 恢复归档。

操作：

- 点击会话：加载详情和消息。
- 点击新建：打开 Agent 选择或直接基于当前 Agent 创建空会话。
- 搜索：调用会话列表接口并重置到第一页。
- 翻页：调用会话列表接口获取下一页。
- 点击删除 icon：调用 `PATCH /conversations/{id}` 将 `status` 改为
  `archived`，然后从 `/chat` 列表移除。
- 查看更多或管理入口：跳转 `/conversations`。

归档语义：

- `/chat` 中的删除 icon 不做软删除，只归档。
- 归档后该会话不再出现在 `/chat` 默认列表中。
- 归档会话仍可在 `/conversations` 中通过包含归档或状态筛选找到。
- 若当前正在查看的会话被归档，主消息区回到未选择会话状态。

### 4.4 Agent 选择

Agent 是对话的核心上下文，不能让用户输入 ID。

交互：

- 顶部使用 Select 选择 Agent。
- 选项展示 Agent 名称、状态、默认模型。
- 只允许选择可运行 Agent。
- 若 Agent 不可运行，在选项或预览中展示原因。

数据来源：

- 初始可复用 Agent 列表接口筛选 `status=active`。
- 选择后调用
  `GET /api/v1/conversations/agents/{agent_id}/runtime-preview`
  校验运行态。

状态规则：

- 未选择 Agent：输入区禁用，空状态提示先选择 Agent。
- Agent 可运行：允许新建和发送。
- Agent 不可运行：显示阻断原因，不允许发送。

### 4.5 消息流

消息类型：

- user：右侧或主色轻强调。
- assistant：左侧或中性背景，支持 streaming。
- system/opening：轻量提示，不混入普通消息气泡的强层级。
- failed：在 assistant 消息位置展示错误和重试入口。

展示规则：

- 历史消息来自 `GET /messages`。
- 本地发送后立即插入 user 临时消息。
- 收到 `message.created` 后用后端消息 ID 替换本地临时 ID。
- 收到 `message.delta` 时拼接 assistant 临时内容。
- 收到 `message.completed` 后用后端最终 assistant 消息覆盖本地状态。
- 收到 `done` 后移除加载动画并恢复输入区可发送状态。
- 收到 `error` 后把 assistant 消息标记 failed。

滚动规则：

- 每收到一个 `message.delta` chunk，默认滚动到底部，满足实时聊天的主路径体验。
- 如果后续加入“阅读历史时不自动跟随”的能力，应作为增强项单独设计。
- 完成后保持当前位置，不强制打断用户阅读历史。

### 4.6 输入区

控件：

- 多行 textarea。
- 发送 icon button。
- 发送中展示停止或禁用态；一期如果后端不支持取消，可只禁用并展示发送中。
- 支持 `Enter` 发送，`Shift + Enter` 换行。
- 用户点击发送或按 Enter 后，输入框立刻清空。
- 发送期间发送按钮不可点击，直到收到 `done` 或 `error`。
- 输入框清空后，前端内部必须保留本轮 `submittedContent`，用于失败重试。

校验：

- trim 后不能为空。
- 最大 20000 字符。
- 未选择 Agent、无当前会话、会话归档、正在发送时禁用。

发送策略：

- 如果已选 Agent 但没有会话，先创建会话再发消息。
- 如果已有 active 会话，直接调用 SSE 发送。
- 发送期间锁定当前会话，避免切换造成状态串线。
- 前端必须使用 `fetch` 手动处理 POST SSE 响应流，不使用 `EventSource`。

完整时间线：

1. 用户在输入框输入内容，点击发送或按 Enter。
2. 前端保存本轮 `submittedContent`，输入框立刻清空，发送按钮变为不可点击。
3. 消息区域底部出现用户消息气泡，靠右，使用深色背景。
4. 紧接着出现 AI 消息气泡，靠左，使用浅色背景，内容为空并显示加载动画。
5. 前端用 `fetch` 发起 `POST /messages/stream`，手动解析 SSE 流。
6. 每收到一个 `message.delta` chunk，把 `delta` 追加到 AI 气泡，并滚动到底部。
7. 收到 `done` 事件后，加载动画消失，发送按钮恢复可用。
8. 如果请求失败或收到 `error` 事件，AI 气泡显示红色错误提示，发送按钮恢复可用。
   错误气泡提供重试入口，重试时使用本轮保留的 `submittedContent`。

## 5. `/chat` SSE 前端状态机

状态：

- `idle`：无发送任务。
- `creatingConversation`：正在创建会话。
- `connecting`：已发起 SSE 请求，等待首个事件。
- `streaming`：正在接收 delta。
- `completed`：本轮完成。
- `failed`：本轮失败。

事件处理：

- `run.started`：记录 runId，状态转 `streaming`。
- `message.created`：确认 user 和 assistant 后端消息 ID。
- `message.delta`：追加 assistant 文本。
- `message.completed`：替换 assistant 最终消息。
- `run.completed`：刷新会话摘要和会话列表。
- `done`：本轮 SSE 正常结束，移除加载态并恢复输入。
- `error`：标记失败，保留用户输入和错误信息。

失败恢复：

- 鉴权失败：提示管理员检查 Provider 密钥。
- 限流：提示稍后重试。
- 超时：保留 `submittedContent`，允许重试。
- 断网：前端显示连接失败，允许用 `submittedContent` 重试本条用户消息。

## 6. `会话日志` 页面设计

### 6.1 页面目标

`/conversations` 面向管理员和排查人员，用于管理和审计会话。

页面支持：

- 会话列表。
- 搜索标题和最后消息。
- 按 Agent、状态筛选，支持搜索 archived 会话。
- 查看详情和消息历史。
- 归档/恢复。
- 删除。
- 跳转到 `/chat` 继续某个 active 会话。

### 6.2 页面布局

沿用管理页模式：

- 外层使用 `FrameView`。
- 列表使用 `ListTable`。
- 操作列使用 icon button + Tooltip。
- 详情可用抽屉或右侧详情区；一期建议抽屉，避免把页面拆得太重。

列表字段：

- 标题。
- Agent。
- 状态。
- 最后消息摘要。
- 消息数量。
- 最后消息时间。
- 创建时间。

筛选：

- 关键词。
- Agent。
- 状态。
- 是否包含归档。

操作：

- 查看详情。
- 跳转对话。
- 归档/恢复。
- 软删除。

### 6.3 详情抽屉

详情内容：

- 会话基础信息。
- Agent 快照。
- 消息列表。
- 最近一次 run 状态摘要。
- 错误信息，若存在。

说明：

- 详情抽屉只读，不提供沉浸式输入。
- active 会话可提供“继续对话”按钮跳转 `/chat?conversationId=...`。

## 7. `/chat` 与 `/conversations` 的边界

`/chat` 负责：

- 实时对话。
- 当前用户 active 会话搜索、分页和切换。
- 新建会话。
- 当前会话继续发送。
- 将会话归档并从聊天列表移除。

`/conversations` 负责：

- 完整列表。
- 搜索筛选。
- 归档恢复。
- 软删除。
- 排查历史消息和运行错误。

共享：

- domain types。
- JSON service。
- query keys。
- 消息展示基础组件可复用。

不共享：

- `/chat` 的 SSE 临时状态不要放进 React Query cache 直接变异。
- `/conversations` 不接入 SSE。

## 8. 数据和状态管理

React Query 管理：

- 会话列表。
- `/chat` 会话列表关键词和分页参数。
- 会话详情。
- 消息历史。
- Agent runtime preview。

组件本地状态管理：

- 当前输入框内容。
- 本轮已提交但不再显示在输入框中的 `submittedContent`。
- SSE 连接状态。
- 临时 user 消息。
- streaming assistant 文本。
- 自动滚动状态。

完成后同步：

- `message.completed` 后更新本地消息。
- `run.completed` 后 invalidate 当前消息列表和会话列表。
- 页面刷新后完全以服务端消息历史为准。

## 9. 响应式设计

桌面：

- 会话列表栏 + 主聊天区并排。

中等宽度：

- 会话列表栏可折叠。
- 顶部保留 Agent 选择和新建按钮。

移动端：

- 默认只展示主聊天区。
- 会话列表作为抽屉打开。
- 输入区固定底部，但不能遮挡消息底部。

## 10. 空态、加载态和错误态

`/chat` 空态：

- 未选择 Agent：提示选择 Agent 开始对话。
- 已选 Agent 但无会话：展示 opening message 和输入框。
- 会话无消息：展示 opening message。

加载态：

- 会话列表加载：列表 skeleton。
- 消息加载：消息 skeleton。
- SSE connecting：assistant 气泡显示连接中。

错误态：

- Agent 不可运行：顶部警告。
- SSE 失败：assistant 气泡内展示错误和重试。
- 消息历史加载失败：主区内展示重试按钮。

## 11. 与 API 合约映射

JSON 接口：

- `GET /api/v1/conversations`
- `POST /api/v1/conversations`
- `GET /api/v1/conversations/{conversation_id}`
- `PATCH /api/v1/conversations/{conversation_id}`
- `DELETE /api/v1/conversations/{conversation_id}`
- `GET /api/v1/conversations/{conversation_id}/messages`
- `GET /api/v1/conversations/agents/{agent_id}/runtime-preview`

SSE 接口：

- `POST /api/v1/conversations/{conversation_id}/messages/stream`

前端 service：

- JSON 接口走共享 `request<T>()`。
- SSE 接口由 `streamConversationMessage()` 单独封装。

## 12. 暂缓项

一期暂缓：

- 停止生成的真实取消协议。
- 对话重命名自动总结。
- token 用量图表。
- 工具调用可视化时间线。
- RAG 引用来源展示。
- Workflow 运行视图。
- 会话批量操作。
- 跨用户会话审计视图。

这些能力等后端运行链路稳定后再扩展。
