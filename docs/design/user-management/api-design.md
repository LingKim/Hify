# 用户管理接口文档

## 1. 设计目标

用户管理接口服务于后台账号管理页面，采用聚合式 CRUD。

接口目标：

- 支持用户列表、详情、创建、编辑、软删除
- 支持启用、禁用、重置密码
- 不暴露 `password_hash` 或明文密码
- 不再接收或返回 `role` / `roleLabel`
- 用户角色展示读取 RBAC 绑定，角色分配由 RBAC 接口负责
- 保持和现有 Hify 接口一致的响应信封、分页结构和字段命名

## 2. 基础约定

### 2.1 路由前缀

```text
/api/v1/users
```

### 2.2 权限要求

| 操作 | 权限 |
|---|---|
| 列表、详情 | `user.read` |
| 创建、更新、启用、禁用、重置密码、删除 | `user.manage` |

禁用或删除最后一个拥有 `rbac.manage` 权限的启用用户时，接口必须拒绝。

### 2.3 响应信封

除 `DELETE` 外，所有接口统一返回：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

列表接口 `data` 使用：

```json
{
  "list": [],
  "total": 0,
  "page": 1,
  "pageSize": 20,
  "totalPages": 0
}
```

### 2.4 字段命名

- 后端内部使用 snake_case
- HTTP JSON 使用 camelCase
- 时间字段使用 ISO 8601 字符串
- 用户 ID、角色 ID 使用数字 ID

## 3. 数据结构

### 3.1 角色引用 `RoleRef`

```json
{
  "id": 1,
  "code": "member",
  "name": "普通用户",
  "status": "enabled",
  "isSystem": true
}
```

### 3.2 用户摘要 `UserSummary`

用于列表页。

```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@hify.ai",
  "roles": [
    {
      "id": 1,
      "code": "admin",
      "name": "管理员",
      "status": "enabled",
      "isSystem": true
    }
  ],
  "isActive": true,
  "lastLoginAt": "2026-05-12T05:00:00Z",
  "createdAt": "2026-05-02T14:15:00Z",
  "updatedAt": "2026-05-12T05:00:00Z"
}
```

### 3.3 用户详情 `UserDetail`

用户详情和编辑回填使用同一结构。

```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@hify.ai",
  "roles": [
    {
      "id": 1,
      "code": "admin",
      "name": "管理员",
      "status": "enabled",
      "isSystem": true
    }
  ],
  "isActive": true,
  "lastLoginAt": "2026-05-12T05:00:00Z",
  "createdAt": "2026-05-02T14:15:00Z",
  "updatedAt": "2026-05-12T05:00:00Z"
}
```

说明：

- `passwordHash` 永远不返回。
- 创建时提交的明文密码只用于生成哈希，接口响应不回显。
- `roles` 只用于展示当前绑定角色；修改角色走 RBAC 用户授权接口。

## 4. 接口列表

### 4.1 获取用户列表

```text
GET /api/v1/users
```

说明：

- 返回分页后的用户摘要列表
- 默认只返回未软删除用户
- 支持关键词、角色 ID 和启用状态筛选

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `page` | `int` | 否 | 默认 `1` |
| `pageSize` | `int` | 否 | 默认 `20`，最大 `100` |
| `keyword` | `string` | 否 | 模糊匹配用户名或邮箱 |
| `roleId` | `int` | 否 | 按 RBAC 角色 ID 筛选 |
| `isActive` | `boolean` | 否 | 是否启用 |

响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "username": "admin",
        "email": "admin@hify.ai",
        "roles": [
          {
            "id": 1,
            "code": "admin",
            "name": "管理员",
            "status": "enabled",
            "isSystem": true
          }
        ],
        "isActive": true,
        "lastLoginAt": null,
        "createdAt": "2026-05-02T14:15:00Z",
        "updatedAt": "2026-05-02T14:15:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "pageSize": 20,
    "totalPages": 1
  }
}
```

### 4.2 获取用户详情

```text
GET /api/v1/users/{user_id}
```

路径参数：

| 参数 | 类型 | 说明 |
|---|---|---|
| `user_id` | `int` | 用户 ID |

响应 `data` 为 `UserDetail`。

### 4.3 创建用户

```text
POST /api/v1/users
```

说明：

- 创建一个未删除用户
- 用户名和邮箱必须在未删除用户中唯一
- 初始密码必填，只用于生成 `password_hash`
- 系统默认绑定内置 `member` 角色

请求体：

```json
{
  "username": "lisa",
  "email": "lisa@hify.ai",
  "password": "ChangeMe123!",
  "isActive": true
}
```

字段规则：

| 字段 | 类型 | 必填 | 规则 |
|---|---|---|---|
| `username` | `string` | 是 | 1-64 字符，不能为空 |
| `email` | `string` | 是 | 合法邮箱，最长 255 字符 |
| `password` | `string` | 是 | 8-128 字符 |
| `isActive` | `boolean` | 否 | 默认 `true` |

响应状态：

- HTTP `201`
- `code` 为 `201`

响应 `data` 为 `UserDetail`。

### 4.4 更新用户

```text
PUT /api/v1/users/{user_id}
```

说明：

- 更新用户基础资料
- 不通过该接口修改密码
- 不通过该接口修改角色
- 不通过该接口软删除用户

请求体：

```json
{
  "username": "lisa",
  "email": "lisa@hify.ai",
  "isActive": true
}
```

字段规则：

| 字段 | 类型 | 必填 | 规则 |
|---|---|---|---|
| `username` | `string` | 是 | 1-64 字符，不能为空 |
| `email` | `string` | 是 | 合法邮箱，最长 255 字符 |
| `isActive` | `boolean` | 是 | 是否启用 |

业务规则：

- 禁止用户禁用当前登录账号自身。
- 若禁用目标用户会导致系统没有启用的 `rbac.manage` 权限持有者，应拒绝。

响应 `data` 为 `UserDetail`。

### 4.5 启用用户

```text
POST /api/v1/users/{user_id}/enable
```

说明：

- 将 `isActive` 设置为 `true`
- 已软删除用户不可启用

请求体：无。

响应 `data` 为 `UserDetail`。

### 4.6 禁用用户

```text
POST /api/v1/users/{user_id}/disable
```

说明：

- 将 `isActive` 设置为 `false`
- 禁用后该用户不能登录
- 认证依赖应拒绝禁用用户继续访问受保护接口

请求体：

```json
{
  "reason": "离职账号"
}
```

字段说明：

- `reason` 当前不落库，仅用于后续审计扩展；当前可选。

业务规则：

- 禁止禁用当前登录用户自身。
- 禁止禁用最后一个启用且拥有 `rbac.manage` 权限的用户。

响应 `data` 为 `UserDetail`。

### 4.7 重置密码

```text
POST /api/v1/users/{user_id}/reset-password
```

说明：

- 管理员为指定用户设置新密码
- 不返回明文密码
- 不返回密码哈希

请求体：

```json
{
  "password": "NewPassword123!"
}
```

字段规则：

| 字段 | 类型 | 必填 | 规则 |
|---|---|---|---|
| `password` | `string` | 是 | 8-128 字符 |

响应：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 2,
    "passwordUpdated": true,
    "updatedAt": "2026-05-12T05:30:00Z"
  }
}
```

### 4.8 删除用户

```text
DELETE /api/v1/users/{user_id}
```

说明：

- 执行软删除
- 不级联删除会话、Agent、知识库、工具等历史业务数据
- 已删除用户不再出现在默认列表中

业务规则：

- 禁止删除当前登录用户自身。
- 禁止删除最后一个启用且拥有 `rbac.manage` 权限的用户。

响应：

- HTTP `204 No Content`
- 无响应体

## 5. 错误语义

| 场景 | HTTP | code | message 示例 |
|---|---|---|---|
| 用户不存在 | 404 | `1002` | `用户不存在` |
| 用户名已存在 | 409 | `1003` | `用户名已存在` |
| 邮箱已存在 | 409 | `1003` | `邮箱已存在` |
| 参数校验失败 | 422 | `1001` | `参数校验失败` |
| 权限不足 | 403 | `1006` | `权限不足` |
| 禁用当前登录用户 | 400 | `1001` | `不能禁用当前登录用户` |
| 删除当前登录用户 | 400 | `1001` | `不能删除当前登录用户` |
| 移除最后一个权限管理员 | 400 | `1001` | `至少需要保留一个权限管理员` |
| 禁用用户访问受保护接口 | 403 | `2005` | `账户已禁用` |

## 6. 排序、搜索与过滤

默认排序：

1. `createdAt` 倒序
2. `id` 倒序

搜索规则：

- `keyword` 同时匹配 `username` 和 `email`
- 模糊匹配，大小写敏感性按数据库默认能力处理

过滤规则：

- `roleId` 通过 `user_role_bindings.role_id` 精确匹配
- `isActive` 精确匹配
- 默认排除 `deletedAt is not null` 的软删除用户

## 7. 前端聚合接口需求

用户管理页面需要的接口：

- 列表：`GET /api/v1/users`
- 新增弹窗提交：`POST /api/v1/users`
- 编辑弹窗回填：`GET /api/v1/users/{user_id}`
- 编辑弹窗提交：`PUT /api/v1/users/{user_id}`
- 启用：`POST /api/v1/users/{user_id}/enable`
- 禁用：`POST /api/v1/users/{user_id}/disable`
- 重置密码：`POST /api/v1/users/{user_id}/reset-password`
- 删除：`DELETE /api/v1/users/{user_id}`

角色选项不再由用户管理页面内置，统一读取 RBAC：

- `GET /api/v1/rbac/roles/options`
- `GET /api/v1/rbac/users/{user_id}/roles`
- `PUT /api/v1/rbac/users/{user_id}/roles`

## 8. 兼容性说明

- `users.role` 已删除，不保留双轨兼容期。
- 用户管理接口不再返回 `role`、`roleLabel`。
- 创建和更新用户接口不再接收 `role`。
- 用户详情和列表不返回 `deletedAt`，因为默认列表不展示已删除用户；若未来需要回收站能力，再新增包含删除状态的查询参数和字段。
- 密码相关接口永远不返回明文密码或哈希。
