# Agent 配置交付检查清单

## 1. 已完成项

- Gate 1 产品设计：完成。
- Gate 2 数据库设计：完成。
- Gate 2 Alembic 迁移：完成。
- Gate 3 API 契约：完成。
- Gate 4 后端实现：完成。
- Gate 4 前端实现：完成。
- Gate 5 后端接口验证：完成。
- Gate 6 前端测试验证：完成。
- Gate 7 API 级 E2E 验证：完成。
- Gate 8 文档 closeout：完成。

## 2. 验证记录

后端验证：

- `backend/.venv/bin/pytest backend/tests/test_agent_configuration_api.py backend/tests/test_llm_provider_api.py backend/tests/test_module_skeletons.py -q`
- `backend/.venv/bin/ruff check backend/app/agent backend/tests/test_agent_configuration_api.py backend/alembic/versions/20260505_0005_create_agent_configuration_tables.py`
- `.venv/bin/alembic upgrade head`

前端验证：

- `pnpm vitest run src/test/agent-configuration-service.test.ts src/test/app.test.tsx src/test/providers.test.tsx`
- `pnpm lint`
- `pnpm exec tsc -p tsconfig.build.json --noEmit`

本地 API E2E：

- `GET /api/v1/llms/providers`
- `POST /api/v1/agents`
- `GET /api/v1/agents`
- `GET /api/v1/agents/{agent_id}`
- `GET /api/v1/agents/{agent_id}/config-preview`
- `PUT /api/v1/agents/{agent_id}`
- `GET /api/v1/agents/{agent_id}/config-preview`

## 3. E2E 验证结果

已验证：

- Workflow 草稿可保存。
- `systemPrompt = null` 可保存。
- 工具 ID 绑定可保存。
- 知识库 ID 绑定可保存。
- 列表返回模型摘要、工具数量、知识库数量。
- 详情返回完整聚合配置。
- 配置预览返回可运行状态和警告。
- 编辑可整体替换工具和知识库绑定。
- 禁用 Agent 后配置预览返回不可运行警告。

未验证：

- 浏览器插件点选验证：Codex in-app browser 后端未发现可连接实例。

已补充验证：

- 删除接口 E2E：`DELETE /api/v1/agents/1` 返回 `204`。
- 删除后详情：`GET /api/v1/agents/1` 返回 `404` 和 `Agent 不存在`。

## 4. 已知限制

- `docs/` 当前被 `.gitignore` 忽略，设计文档需要强制 add。
- 工具和知识库模块未完成，服务层暂缓强存在性校验。
- Workflow 模块未完成，Workflow Agent 只能保存草稿。
- 前端工具和知识库绑定当前是 ID 输入，不是选择器。

## 5. 临时数据

本地 E2E 曾创建一条 Agent 验证记录：

- 名称：`E2E-Agent-配置验证-20260505-已禁用`
- 状态：`disabled`

该记录已按用户确认执行软删除，删除后详情接口返回 `404`。
