# RBAC 交付检查清单

## 1. 后端迁移

已验证：

- `alembic current` 返回 `20260630_0012 (head)`。
- `users.role` 已删除，`users.last_login_at` 保留。
- `admin`、`member` 已归一化为系统角色。
- 本地 `root` 用户已通过 `scripts/seed_root_user.py` 绑定 `admin` 角色，并拥有 `rbac.manage`。

本地开发库曾存在 `20260609_0011` RBAC 草稿迁移，因此保留 no-op 兼容迁移，让旧库和新库进入同一条 Alembic 链。

## 2. 后端测试

已通过：

```text
backend/.venv/bin/pytest backend/tests/test_foundation.py backend/tests/test_user_management_api.py backend/tests/test_rbac_api.py backend/tests/test_agent_configuration_api.py backend/tests/test_conversation_api.py backend/tests/test_knowledge_api.py backend/tests/test_llm_provider_api.py backend/tests/test_tool_api.py backend/tests/test_tool_route_contract.py -q
```

结果：

```text
42 passed
```

补充验证：

- `backend/.venv/bin/ruff check ...` 通过。
- `git diff --check` 通过。
- `backend/.venv/bin/python -m compileall -q backend/app` 通过。

## 3. Curl Checkpoint

服务入口：

```text
backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

认证：

```bash
curl -s -i -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"account":"root","password":"123456"}'
```

结果：`200 OK`，返回 `roles` 和 `permissions`，不返回 `role` / `roleLabel`。

RBAC 读接口：

```bash
curl -s -i http://127.0.0.1:8000/api/v1/auth/me -H 'Authorization: Bearer <root-token>'
curl -s -i 'http://127.0.0.1:8000/api/v1/rbac/roles?page=1&pageSize=10' -H 'Authorization: Bearer <root-token>'
curl -s -i 'http://127.0.0.1:8000/api/v1/rbac/permissions?module=rbac' -H 'Authorization: Bearer <root-token>'
curl -s -i 'http://127.0.0.1:8000/api/v1/rbac/roles/options?keyword=admin' -H 'Authorization: Bearer <root-token>'
```

结果：均为 `200 OK`，响应信封为 `{ code, message, data }`。

RBAC 写接口：

```bash
curl -s -i -X POST http://127.0.0.1:8000/api/v1/rbac/roles -H 'Content-Type: application/json' -H 'Authorization: Bearer <root-token>' -d '{"code":"curl_ops","name":"Curl 运维","description":"curl checkpoint role","status":"enabled","permissionIds":[113]}'
curl -s -i http://127.0.0.1:8000/api/v1/rbac/roles/101 -H 'Authorization: Bearer <root-token>'
curl -s -i -X PUT http://127.0.0.1:8000/api/v1/rbac/roles/101 -H 'Content-Type: application/json' -H 'Authorization: Bearer <root-token>' -d '{"code":"curl_ops","name":"Curl 运维更新","description":"curl checkpoint role updated","status":"enabled"}'
curl -s -i -X PUT http://127.0.0.1:8000/api/v1/rbac/roles/101/permissions -H 'Content-Type: application/json' -H 'Authorization: Bearer <root-token>' -d '{"permissionIds":[113]}'
curl -s -i -X POST http://127.0.0.1:8000/api/v1/rbac/roles/101/disable -H 'Authorization: Bearer <root-token>'
curl -s -i -X POST http://127.0.0.1:8000/api/v1/rbac/roles/101/enable -H 'Authorization: Bearer <root-token>'
curl -s -i -X DELETE http://127.0.0.1:8000/api/v1/rbac/roles/101 -H 'Authorization: Bearer <root-token>'
```

结果：创建返回 `201 Created`；详情、更新、权限替换、启用、禁用返回 `200 OK`；删除返回 `204 No Content`。

用户管理和用户授权：

```bash
curl -s -i -X POST http://127.0.0.1:8000/api/v1/users -H 'Content-Type: application/json' -H 'Authorization: Bearer <root-token>' -d '{"username":"curl_user_0630","email":"curl_user_0630@hify.local","password":"CurlUser123!","isActive":true}'
curl -s -i 'http://127.0.0.1:8000/api/v1/users?keyword=curl_user_0630&roleId=3&isActive=true' -H 'Authorization: Bearer <root-token>'
curl -s -i http://127.0.0.1:8000/api/v1/users/24 -H 'Authorization: Bearer <root-token>'
curl -s -i -X PUT http://127.0.0.1:8000/api/v1/users/24 -H 'Content-Type: application/json' -H 'Authorization: Bearer <root-token>' -d '{"username":"curl_user_0630_edit","email":"curl_user_0630_edit@hify.local","isActive":true}'
curl -s -i http://127.0.0.1:8000/api/v1/rbac/users/24/roles -H 'Authorization: Bearer <root-token>'
curl -s -i -X PUT http://127.0.0.1:8000/api/v1/rbac/users/24/roles -H 'Content-Type: application/json' -H 'Authorization: Bearer <root-token>' -d '{"roleIds":[101]}'
curl -s -i -X POST http://127.0.0.1:8000/api/v1/users/24/reset-password -H 'Content-Type: application/json' -H 'Authorization: Bearer <root-token>' -d '{"password":"NewCurlUser123!"}'
curl -s -i -X POST http://127.0.0.1:8000/api/v1/users/24/disable -H 'Content-Type: application/json' -H 'Authorization: Bearer <root-token>' -d '{"reason":"curl checkpoint"}'
curl -s -i -X POST http://127.0.0.1:8000/api/v1/users/24/enable -H 'Authorization: Bearer <root-token>'
curl -s -i -X DELETE http://127.0.0.1:8000/api/v1/users/24 -H 'Authorization: Bearer <root-token>'
```

结果：创建返回 `201 Created` 并默认绑定 `member`；列表、详情、更新、授权、重置密码、启用、禁用返回 `200 OK`；删除返回 `204 No Content`；删除后详情返回 `404 用户不存在`。

权限负例：

```bash
curl -s -i -X POST http://127.0.0.1:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"account":"curl_user_0630_edit","password":"NewCurlUser123!"}'
curl -s -i http://127.0.0.1:8000/api/v1/users -H 'Authorization: Bearer <limited-user-token>'
```

结果：测试用户仅拥有 `rbac.read`；访问 `/api/v1/users` 返回 `403`，响应为 `{"code":1006,"message":"权限不足","data":null}`。

## 4. Checkpoint 中发现并修复的问题

- 旧本地库的 `alembic_version` 指向 `20260609_0011`，仓库缺少该 revision。已增加兼容 no-op revision。
- 旧 RBAC 草稿表缺少 `roles.status` 和 `permissions.is_system`。正式迁移已兼容补列。
- 旧草稿 seed 中 `admin`、`member` 不是系统角色。已增加 seed 归一化迁移。
- `PUT /rbac/roles/{role_id}/permissions` 在替换到历史软删除权限时响应权限为空。已改为角色详情直接查询 active 绑定，并补充接口测试。

## 5. 剩余事项

- 本地开发库保留历史草稿 seed，例如 `super_admin` 和 `xxx:view` 权限点；正式新库不会生成这些历史数据。
- 前端 RBAC 页面、用户管理页面和权限感知已完成第一轮接入。
- 前端聚焦验证已通过：

```text
./node_modules/.bin/tsc --noEmit
./node_modules/.bin/vitest run src/test/app.test.tsx
./node_modules/.bin/oxlint src/domain/rbac src/domain/user-management src/domain/auth src/pages/rbac src/pages/user-management src/app/router src/app/layouts src/test/app.test.tsx
```

结果：`app.test.tsx` 为 `12 passed`，并覆盖普通用户访问 `/rbac` 的 403 行为。

- 真实浏览器已验证 root 访问 `http://127.0.0.1:5174/rbac`：页面、侧边栏“权限管理”和“新增角色”按钮可见；控制台只有 `favicon.ico` 404。
- Playwright CLI 因 npm 拉取 `@playwright/cli` 受网络/代理限制失败；内置浏览器工具的普通 member 登录动作又被工具额度限制中断，因此普通 member 的真实浏览器 E2E 尚未完成。
- 本轮为普通 member 浏览器验证创建了临时用户 `e2e_member_rbac_1782798453304`（id `25`），清理请求被同一工具额度限制拦截；下一次具备本地 API 操作权限后应优先删除该测试用户。
