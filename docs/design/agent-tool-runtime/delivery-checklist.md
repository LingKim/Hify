# Agent 工具运行闭环交付清单

## 2026-05-24 实现范围

后端：

- LiteLLM executor 新增工具决策调用封装，支持 `tools` 参数和
  `tool_calls` 归一化。
- Conversation SSE 支持 `tool.started`、`tool.completed`、`tool.failed`。
- Conversation 消息响应新增 `toolCalls`。
- Conversation 运行时支持单轮工具调用：模型决策、HTTP 工具执行、工具结果回喂、
  最终 assistant 流式输出。
- ToolService 新增 conversation 来源执行能力，写入
  `tool_execution_logs.source = conversation`，不覆盖工具管理页测试状态。
- Agent 保存时校验启用工具必须存在且 `status = enabled`。

前端：

- Agent 配置页工具绑定从占位提示改为真实工具多选。
- Chat SSE parser 支持三个工具事件。
- Chat 消息气泡展示工具调用摘要。
- Conversation 类型补充 `toolCalls` 和工具 SSE 事件类型。

## 自动化验证

已运行：

- `backend/.venv/bin/ruff check backend/app/agent backend/app/conversation backend/app/llm/executor.py backend/app/tool/service.py backend/tests/test_conversation_api.py backend/tests/test_agent_configuration_api.py`
  - 结果：通过。
- `backend/.venv/bin/python -m compileall -q backend/app`
  - 结果：通过。
- `cd frontend && pnpm lint`
  - 结果：通过，`0 warnings and 0 errors`。
- `cd frontend && pnpm vitest run src/test/agent-configuration-service.test.ts src/test/app.test.tsx`
  - 结果：通过，`12 passed`。
  - 备注：测试环境输出 Ant Design/JSDOM 的 `getComputedStyle` pseudo-elements
    warning，既有测试中已存在，不影响本轮断言结果。
- `cd frontend && pnpm exec tsc -p tsconfig.build.json --noEmit`
  - 结果：通过。
- `backend/.venv/bin/pytest backend/tests/test_conversation_api.py::test_stream_message_executes_bound_tool_and_exposes_tool_calls -q`
  - 结果：通过，`1 passed`。
- `backend/.venv/bin/pytest backend/tests/test_conversation_api.py backend/tests/test_agent_configuration_api.py backend/tests/test_tool_api.py -q`
  - 结果：通过，`11 passed`。

## 接口测试状态

已新增后端接口级测试：

- `backend/tests/test_conversation_api.py::test_stream_message_executes_bound_tool_and_exposes_tool_calls`

该测试覆盖：

- Agent 绑定 enabled HTTP 工具。
- 模型返回 `weather_lookup` tool call。
- SSE 返回 `tool.started` 和 `tool.completed`。
- 工具密钥不出现在 SSE 响应中。
- assistant 历史消息返回 `toolCalls`。
- 工具调用写入 `tool_execution_logs.source = conversation`。
- 工具日志请求头脱敏。

验证时 Docker 中已提供 PostgreSQL 和 Redis：

- PostgreSQL：`myPostGres postgres:18.1`，端口 `5432`。
- Redis：`myRedis redis:latest`，端口 `6379`。

接口测试已基于该 PostgreSQL 实例完成。

## 已知限制

- 本期只支持一轮工具调用；如果模型第二次仍请求工具，本轮不会继续递归执行。
- 工具执行失败不会直接终止 SSE，但二次模型生成失败仍会通过 `error` 终止。
- 会话日志页面展示工具调用摘要，不提供工具执行日志详情抽屉。
- `tool_execution_logs.conversation_id` 和 `run_id` 仍按现有设计保持无外键，只通过
  索引用于查询。
