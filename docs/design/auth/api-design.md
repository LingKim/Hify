# 登录与鉴权接口设计

## 1. 基础约定

- 路由前缀：`/api/v1/auth`
- 普通 JSON 接口使用统一 `Result<T>` 响应信封。
- `POST /auth/login` 公开访问。
- 其他业务接口默认要求 `Authorization: Bearer <token>`。

## 2. 登录

```text
POST /api/v1/auth/login
```

请求体：

```json
{
  "account": "root",
  "password": "123456"
}
```

响应：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "accessToken": "jwt",
    "tokenType": "Bearer",
    "expiresIn": 3600,
    "user": {
      "id": 1,
      "username": "root",
      "email": "root@hify.local",
      "role": "admin",
      "roleLabel": "管理员"
    }
  }
}
```

错误：

- `2001`：用户名或密码错误。
- `2005`：账户已禁用。

## 3. 当前用户

```text
GET /api/v1/auth/me
```

响应 `data`：

```json
{
  "id": 1,
  "username": "root",
  "email": "root@hify.local",
  "role": "admin",
  "roleLabel": "管理员"
}
```

错误：

- `2002`：Token 过期。
- `2003`：Token 无效或未登录。
- `2005`：账户已禁用。

## 4. 受保护接口

除 `health`、`ready`、`metrics`、`POST /auth/login` 外，业务接口都要求登录。当前阶段 `admin` 和 `member` 可访问相同功能，后续 RBAC 落地时再在依赖层细分权限。

会话接口必须使用当前登录用户隔离数据：列表、详情、更新、删除、消息读取和 SSE 发送都不能跨用户访问。
