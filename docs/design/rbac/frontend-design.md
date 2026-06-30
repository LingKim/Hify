# RBAC 前端设计

## 1. 页面范围

本期新增 `/rbac` 权限管理页面，并同步调整 `/users` 用户管理页面。

`/rbac` 覆盖：

- 角色列表。
- 角色新增、编辑。
- 角色启用、禁用、软删除。
- 角色权限替换。
- 权限点展示和选择。

`/users` 调整：

- 用户列表展示 `roles` 数组，不再展示 `role` / `roleLabel`。
- 新增和编辑用户不再提交角色。
- 新用户默认角色由后端绑定为 `member`。
- 用户角色分配通过 RBAC 用户授权接口完成。
- 用户筛选改为 `roleId`。

## 2. 前端模块结构

新增：

```text
frontend/src/domain/rbac/
├── api.ts
├── components.tsx
├── queries.ts
├── service.ts
└── types.ts

frontend/src/pages/rbac/RbacPage.tsx
```

沿用项目现有 domain 约定：

```text
components -> queries -> service -> api -> shared request
```

## 3. 路由和导航

新增路由：

```text
/rbac
```

新增侧边栏入口：

```text
权限管理
```

用户管理保留：

```text
/users
```

## 4. RBAC 页面交互

### 4.1 列表

角色列表使用 `ListTable`：

- 关键词筛选：角色编码、名称、描述。
- 状态筛选：启用 / 禁用。
- 表格字段：角色、状态、系统角色、用户数、权限数、更新时间。

### 4.2 表单

角色新增和编辑使用 `FormDialog`：

- 角色编码。
- 角色名称。
- 描述。
- 状态。
- 权限多选。

编辑时角色编码禁用，避免破坏后端权限依赖中的稳定 code。

### 4.3 权限替换

角色列表操作列提供“权限”按钮，打开权限多选弹窗，提交：

```text
PUT /api/v1/rbac/roles/{role_id}/permissions
```

## 5. 用户管理联动

用户管理列表使用角色 tags 展示 `roles`。

操作列新增“分配角色”按钮，打开角色多选弹窗，提交：

```text
PUT /api/v1/rbac/users/{user_id}/roles
```

角色选项来自：

```text
GET /api/v1/rbac/roles/options
```

## 6. 权限感知

前端从登录响应和 `/auth/me` 读取：

```json
{
  "roles": [],
  "permissions": []
}
```

已接入：

- 侧边栏菜单按 `permissions` 隐藏无权业务入口。
- 业务路由按页面权限进行守卫，无权限时展示 403 页面。
- `/rbac` 写操作按钮要求 `rbac.manage`。
- `/users` 新增、编辑、启停、重置密码、删除要求 `user.manage`。
- `/users` 分配角色要求 `rbac.manage`。

页面级读取权限：

| 页面 | 进入权限 |
| --- | --- |
| `/providers` | `provider.read` 或 `provider.manage` |
| `/agents` | `agent.read` 或 `agent.manage` |
| `/tools` | `tool.read` 或 `tool.manage` |
| `/knowledge` | `knowledge.read` 或 `knowledge.manage` |
| `/chat` | `conversation.use` |
| `/conversations` | `conversation.read` 或 `conversation.manage` |
| `/users` | `user.read` 或 `user.manage` |
| `/rbac` | `rbac.read` 或 `rbac.manage` |

## 7. 验证

已验证：

- `./node_modules/.bin/tsc --noEmit`
- `./node_modules/.bin/vitest run src/test/app.test.tsx`，`12 passed`
- `./node_modules/.bin/oxlint src/domain/rbac src/domain/user-management src/domain/auth src/pages/rbac src/pages/user-management src/app/router src/app/layouts src/test/app.test.tsx`

其中 `app.test.tsx` 覆盖：

- 登录后返回原目标页。
- `/users` 和 `/rbac` 路由渲染。
- 缺少权限访问 `/rbac` 时展示 403。

真实浏览器验证：

- 通过 root 登录 `http://127.0.0.1:5174/rbac`，确认 RBAC 页面、侧边栏“权限管理”和“新增角色”按钮可见。
- 控制台仅发现 `favicon.ico` 404，未发现业务接口报错。
- Playwright CLI 因 npm 拉取 `@playwright/cli` 受网络/代理限制未能运行；随后使用内置浏览器工具完成 admin 页面验证。
- 普通 member 用户的浏览器登录验证被工具额度限制中断；该路径已有单元测试覆盖，但尚未完成真实浏览器 E2E。
