# 工具集成交付清单

## 2026-05-23 后端交付验证

### 数据库迁移

- `cd backend && .venv/bin/alembic upgrade head`
- 结果：通过，已升级到 `20260523_0010_create_tool_tables`。

### 自动化检查

- `backend/.venv/bin/ruff check backend/app/tool backend/tests/test_tool_api.py backend/tests/test_tool_route_contract.py backend/alembic/versions/20260523_0010_create_tool_tables.py`
- 结果：通过。
- `backend/.venv/bin/pytest backend/tests/test_tool_api.py backend/tests/test_tool_route_contract.py -q`
- 结果：通过，`5 passed`。

### curl 验证

本轮使用本地后端入口 `http://127.0.0.1:8000`，登录账号 `root`，密码 `123456`，所有业务请求均携带 `Authorization: Bearer <token>`。

| 顺序 | 接口 | 代表命令 | 结果 |
| --- | --- | --- | --- |
| 1 | `POST /api/v1/auth/login` | `curl -H "Content-Type: application/json" -d '{"account":"root","password":"123456"}'` | HTTP 200，返回 access token |
| 2 | `GET /api/v1/tools/execution-preview` | `curl -H "Authorization: Bearer <token>" /api/v1/tools/execution-preview` | HTTP 200，`data.module = tool` |
| 3 | `POST /api/v1/tools` | 创建 `enabled` HTTP GET 工具，目标 `https://example.com/` | HTTP 201，返回工具详情 |
| 4 | `GET /api/v1/tools` | 按 `keyword`、`status=enabled` 查询 | HTTP 200，列表包含新工具 |
| 5 | `GET /api/v1/tools/options` | 按 `keyword`、`status=enabled` 查询 | HTTP 200，选项包含新工具 |
| 6 | `GET /api/v1/tools/{tool_id}` | 读取新工具详情 | HTTP 200，参数和鉴权信息符合契约 |
| 7 | `PUT /api/v1/tools/{tool_id}` | 从 `authType=none` 更新为 `api_key_header` | HTTP 200，密钥脱敏返回 |
| 8 | `PUT /api/v1/tools/{tool_id}` | `secretValue=null` 更新同一工具 | HTTP 200，保留原密钥脱敏值 |
| 9 | `POST /api/v1/tools/{tool_id}/execute-test` | `{"parameters":{"city":"Hangzhou"},"timeoutSeconds":10}` | HTTP 200，`data.status = success`，上游 HTTP 200 |
| 10 | `GET /api/v1/tools/{tool_id}/execution-logs` | 按 `source=test&status=success` 查询 | HTTP 200，列表包含本次执行日志 |
| 11 | `POST /api/v1/tools/import-openapi/preview` | OpenAPI 3.0 单 operation 草稿预览 | HTTP 200，生成 `sourceType=openapi` 草稿 |
| 12 | `DELETE /api/v1/tools/{tool_id}` | 删除未绑定工具 | HTTP 204 |
| 13 | `DELETE /api/v1/tools/{tool_id}` | 创建 Agent 绑定后删除工具 | HTTP 400，业务码 `6005 TOOL_IN_USE` |

验证后已清理 curl 创建的测试 Agent 和测试工具。后端日志中本轮 curl 请求没有 traceback。

### curl 发现并修复的问题

- `GET /api/v1/tools/options` 原实现使用 `status_value` 查询参数，与 API 文档的 `status` 不一致；已改为 `status` alias。
- 从 `authType=none` 切换到带密钥鉴权时，旧 auth 软删除和新 auth 插入可能触发活跃唯一约束；已补充 flush 和回归测试。
- URL 安全校验已补充对 `localhost`、回环地址、内网地址、link-local、metadata service 等明显危险目标的拦截。

## 2026-05-23 前端交付验证

### 自动化检查

- `cd frontend && pnpm lint`
- 结果：通过，`0 warnings and 0 errors`。
- `cd frontend && pnpm vitest run src/test/request.test.ts src/test/list-table.test.tsx`
- 结果：通过，`13 passed`。

### 浏览器冒烟

使用本地前端 `http://127.0.0.1:5173/tools` 和后端 `http://127.0.0.1:8000`。

- 登录 `root / 123456` 后可进入 `/tools`。
- 工具列表加载成功。
- 新增工具弹窗打开成功。
- OpenAPI 导入弹窗提交 Weather API 单 operation 后成功生成创建草稿。
- 草稿创建工具成功，列表出现新工具。
- 测试执行弹窗按 `city=Hangzhou` 调用后端执行接口，返回并展示执行结果。
- 本轮 UI 冒烟创建的测试工具已清理。
