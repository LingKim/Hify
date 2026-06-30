# RBAC 权限管理接口设计

## 1. 设计目标

RBAC 接口用于替代现有 `users.role` 单字段权限模型，提供角色管理、权限查看、
角色授权、用户授权和当前用户权限快照。

接口目标：

- 权限判断以 RBAC 绑定为准，不再兼容 `users.role`。
- 权限点由系统 seed 管理，接口只允许查看权限，不允许页面新增权限 code。
- 角色可以由管理员维护，但系统角色 `admin`、`member` 不允许删除。
- 用户可以绑定多个角色。
- `/auth/me` 返回当前用户的角色和权限快照，供前端菜单、路由和按钮守卫使用。
- 所有写操作必须防止移除最后一个拥有 `rbac.manage` 权限的启用用户。

## 2. 基础约定

### 2.1 路由前缀

RBAC 路由前缀：

```text
/api/v1/rbac
```

鉴权快照扩展复用：

```text
/api/v1/auth/me
```

### 2.2 响应信封

除 `DELETE` 外，所有接口统一返回：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

分页接口的 `data` 使用：

```json
{
  "list": [],
  "total": 0,
  "page": 1,
  "pageSize": 20,
  "totalPages": 0
}
```

### 2.3 字段命名

- 后端 Python 和数据库使用 snake_case。
- HTTP JSON 使用 camelCase。
- 角色、权限 code 使用小写英文、点号分隔。
- 时间字段使用 ISO 8601 字符串。

### 2.4 权限要求

- `rbac.read`：查看角色、权限、用户授权。
- `rbac.manage`：创建、编辑、启用、禁用、删除角色，修改角色权限和用户角色。
- `/auth/me`：只要求登录。

## 3. 数据结构

### 3.1 角色摘要 `RoleSummary`

```json
{
  "id": 1,
  "code": "admin",
  "name": "管理员",
  "description": "系统管理员，拥有全部平台权限",
  "status": "enabled",
  "isSystem": true,
  "userCount": 1,
  "permissionCount": 15,
  "createdAt": "2026-06-30T00:00:00Z",
  "updatedAt": "2026-06-30T00:00:00Z"
}
```

### 3.2 角色详情 `RoleDetail`

```json
{
  "id": 1,
  "code": "admin",
  "name": "管理员",
  "description": "系统管理员，拥有全部平台权限",
  "status": "enabled",
  "isSystem": true,
  "permissions": [
    {
      "id": 1,
      "code": "provider.manage",
      "name": "管理模型提供商",
      "module": "provider",
      "action": "manage",
      "description": "管理模型提供商",
      "isSystem": true
    }
  ],
  "createdAt": "2026-06-30T00:00:00Z",
  "updatedAt": "2026-06-30T00:00:00Z"
}
```

### 3.3 权限项 `PermissionItem`

```json
{
  "id": 1,
  "code": "provider.manage",
  "name": "管理模型提供商",
  "module": "provider",
  "moduleLabel": "模型提供商",
  "action": "manage",
  "actionLabel": "管理",
  "description": "管理模型提供商",
  "isSystem": true
}
```

### 3.4 用户授权摘要 `UserRoleAssignment`

```json
{
  "userId": 1,
  "username": "root",
  "email": "root@hify.local",
  "isActive": true,
  "roles": [
    {
      "id": 1,
      "code": "admin",
      "name": "管理员",
      "status": "enabled",
      "isSystem": true
    }
  ],
  "permissions": ["provider.manage", "rbac.manage"]
}
```

### 3.5 当前用户权限快照 `CurrentUser`

`GET /api/v1/auth/me`、`POST /api/v1/auth/login` 的用户对象改为：

```json
{
  "id": 1,
  "username": "root",
  "email": "root@hify.local",
  "roles": [
    {
      "id": 1,
      "code": "admin",
      "name": "管理员",
      "status": "enabled",
      "isSystem": true
    }
  ],
  "permissions": [
    "provider.read",
    "provider.manage",
    "rbac.read",
    "rbac.manage"
  ]
}
```

兼容说明：

- RBAC 落地后，不再返回 `role` 和 `roleLabel` 作为权限依据。
- 前端菜单、路由和按钮只读取 `permissions`。
- 如展示主角色，可由前端取 `roles[0]` 或由后续产品设计定义展示规则。

## 4. 接口列表

### 4.1 获取角色列表

```text
GET /api/v1/rbac/roles
```

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `page` | `int` | 否 | 默认 `1` |
| `pageSize` | `int` | 否 | 默认 `20`，最大 `100` |
| `keyword` | `string` | 否 | 搜索角色 code、名称、说明 |
| `status` | `string` | 否 | `enabled`、`disabled` |
| `isSystem` | `boolean` | 否 | 是否系统角色 |

响应：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "code": "admin",
        "name": "管理员",
        "description": "系统管理员，拥有全部平台权限",
        "status": "enabled",
        "isSystem": true,
        "userCount": 1,
        "permissionCount": 15,
        "createdAt": "2026-06-30T00:00:00Z",
        "updatedAt": "2026-06-30T00:00:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "pageSize": 20,
    "totalPages": 1
  }
}
```

### 4.2 获取角色详情

```text
GET /api/v1/rbac/roles/{role_id}
```

响应 `data` 使用 `RoleDetail`。

### 4.3 创建角色

```text
POST /api/v1/rbac/roles
```

请求体：

```json
{
  "code": "ops",
  "name": "运维",
  "description": "负责模型、工具和知识库配置",
  "status": "enabled",
  "permissionIds": [1, 2, 3]
}
```

规则：

- `code` 必填，只允许小写字母、数字、下划线和短横线。
- `code` 在未删除角色中唯一。
- 新建角色默认 `isSystem = false`。
- `permissionIds` 可为空，表示先创建空角色。

响应：

- HTTP `201`
- `data` 使用 `RoleDetail`

### 4.4 更新角色

```text
PUT /api/v1/rbac/roles/{role_id}
```

请求体：

```json
{
  "code": "ops",
  "name": "运维",
  "description": "负责模型、工具和知识库配置",
  "status": "enabled"
}
```

规则：

- 系统角色不允许修改 `code`。
- 系统角色允许修改 `name`、`description` 和权限绑定。
- 禁用角色时，该角色不再参与权限解析。
- 如果禁用会导致没有启用用户拥有 `rbac.manage`，返回 400。

响应 `data` 使用 `RoleDetail`。

### 4.5 启用角色

```text
POST /api/v1/rbac/roles/{role_id}/enable
```

响应 `data` 使用 `RoleDetail`。

### 4.6 禁用角色

```text
POST /api/v1/rbac/roles/{role_id}/disable
```

规则：

- 如果禁用会导致没有启用用户拥有 `rbac.manage`，返回 400。

响应 `data` 使用 `RoleDetail`。

### 4.7 删除角色

```text
DELETE /api/v1/rbac/roles/{role_id}
```

规则：

- 系统角色不能删除。
- 删除角色采用软删除。
- 同步软删除该角色的用户绑定和权限绑定。
- 如果删除会导致没有启用用户拥有 `rbac.manage`，返回 400。

响应：

- HTTP `204`

### 4.8 获取权限列表

```text
GET /api/v1/rbac/permissions
```

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `module` | `string` | 否 | 按模块过滤 |
| `action` | `string` | 否 | 按动作过滤 |
| `keyword` | `string` | 否 | 搜索权限 code、名称、说明 |

响应：

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "code": "provider.manage",
      "name": "管理模型提供商",
      "module": "provider",
      "moduleLabel": "模型提供商",
      "action": "manage",
      "actionLabel": "管理",
      "description": "管理模型提供商",
      "isSystem": true
    }
  ]
}
```

### 4.9 更新角色权限

```text
PUT /api/v1/rbac/roles/{role_id}/permissions
```

请求体：

```json
{
  "permissionIds": [1, 2, 3]
}
```

规则：

- 采用整体替换语义。
- `permissionIds` 中的权限必须存在且未删除。
- 如果移除权限会导致没有启用用户拥有 `rbac.manage`，返回 400。
- 空数组表示清空该角色全部权限，系统角色也允许清空，但必须满足防自锁规则。

响应 `data` 使用 `RoleDetail`。

### 4.10 获取用户角色

```text
GET /api/v1/rbac/users/{user_id}/roles
```

响应 `data` 使用 `UserRoleAssignment`。

### 4.11 更新用户角色

```text
PUT /api/v1/rbac/users/{user_id}/roles
```

请求体：

```json
{
  "roleIds": [1, 2]
}
```

规则：

- 采用整体替换语义。
- `roleIds` 不能为空，用户至少保留一个角色。
- 角色必须存在、未删除且 `status = enabled`。
- 如果移除角色会导致没有启用用户拥有 `rbac.manage`，返回 400。
- 禁用或软删除用户可以修改角色，但不会参与权限解析。

响应 `data` 使用 `UserRoleAssignment`。

### 4.12 获取角色选项

```text
GET /api/v1/rbac/roles/options
```

说明：

- 给用户授权、筛选器和表单选择器使用。
- 默认只返回启用且未删除角色。

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `keyword` | `string` | 否 | 搜索 code 或名称 |
| `includeDisabled` | `boolean` | 否 | 是否包含禁用角色，默认 `false` |

响应：

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "value": 1,
      "label": "管理员",
      "code": "admin",
      "isSystem": true
    }
  ]
}
```

## 5. 用户管理接口调整

RBAC 落地后，用户管理接口不再直接读写单一 `role` 字段。

### 5.1 用户摘要调整

`UserSummary` 和 `UserDetail` 删除：

- `role`
- `roleLabel`

新增：

```json
{
  "roles": [
    {
      "id": 1,
      "code": "admin",
      "name": "管理员",
      "status": "enabled",
      "isSystem": true
    }
  ]
}
```

### 5.2 用户列表筛选调整

`GET /api/v1/users` 查询参数：

- 删除 `role`
- 新增 `roleId`

### 5.3 创建和编辑用户调整

`POST /api/v1/users` 和 `PUT /api/v1/users/{user_id}` 删除请求字段：

- `role`

用户创建后的默认角色：

- 如果请求体不包含 `roleIds`，后端默认分配 `member`。
- 若产品希望创建用户时直接分配角色，可在用户管理 API 中新增可选
  `roleIds`。本期推荐角色分配走 `/rbac/users/{user_id}/roles`，避免用户
  CRUD 和授权职责混在一起。

## 6. 权限接入建议

### 6.1 后端依赖

后端新增依赖：

```python
require_permission("provider.manage")
```

建议首批替换：

| 模块 | 读接口 | 写接口 |
|---|---|---|
| Provider | `provider.read` | `provider.manage` |
| Agent | `agent.read` | `agent.manage` |
| Tool | `tool.read` | `tool.manage` |
| Knowledge | `knowledge.read` | `knowledge.manage` |
| Conversation | `conversation.read` / `conversation.use` | `conversation.manage` |
| User | `user.read` | `user.manage` |
| RBAC | `rbac.read` | `rbac.manage` |

说明：

- `conversation.use` 用于 `/chat` 发消息和创建本人会话。
- `conversation.read` 用于读取本人会话和消息。
- `conversation.manage` 用于后台会话日志管理能力；当前若没有跨用户管理接口，
  可先只作为菜单和后续扩展权限。

### 6.2 前端守卫

前端根据 `/auth/me` 的 `permissions`：

- 隐藏无权限菜单。
- 无权限访问路由时展示 403 页面或跳转首页。
- 操作按钮根据对应 `manage` 权限隐藏或禁用。

前端不应只依赖菜单隐藏作为安全边界，后端接口仍必须做权限校验。

## 7. 错误语义

建议新增 `RbacErrorCode`：

| code | 名称 | HTTP | 说明 |
|---|---|---|---|
| `8001` | `ROLE_NOT_FOUND` | 404 | 角色不存在或已删除 |
| `8002` | `PERMISSION_NOT_FOUND` | 404 | 权限不存在或已删除 |
| `8003` | `ROLE_CODE_EXISTS` | 409 | 角色 code 已存在 |
| `8004` | `SYSTEM_ROLE_PROTECTED` | 400 | 系统角色不允许执行该操作 |
| `8005` | `RBAC_SELF_LOCK_RISK` | 400 | 操作会导致系统没有权限管理员 |
| `8006` | `ROLE_DISABLED` | 400 | 角色已禁用，不能分配 |
| `8007` | `EMPTY_ROLE_ASSIGNMENT` | 400 | 用户至少需要一个角色 |

通用错误继续复用：

- `403 FORBIDDEN`：当前用户缺少接口所需权限。
- `400 VALIDATION_ERROR`：请求参数不合法。

## 8. 验收清单

- `/auth/me` 返回当前用户 `roles` 和 `permissions`。
- 管理员可以创建、编辑、禁用、启用、删除非系统角色。
- 管理员可以查看权限列表。
- 管理员可以给角色整体替换权限。
- 管理员可以给用户整体替换角色。
- 系统阻止删除、禁用或解除最后一个拥有 `rbac.manage` 的启用用户。
- 非授权用户访问 RBAC 写接口返回 403。
- 用户管理接口不再依赖 `users.role`。
- 前端可以用 `permissions` 控制菜单、路由和操作按钮。
