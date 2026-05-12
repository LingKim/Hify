# 登录与鉴权前端设计

## 1. 路由

- `/login`：公开登录页。
- 其他应用路由通过路由守卫检查本地 token 和 `/auth/me`。
- 未登录访问业务页跳转 `/login`，并记录原始目标；登录成功后回到原目标。
- 已登录访问 `/login` 自动回首页。

## 2. 请求与状态

- token 存储键：`hify-access-token`。
- `shared/auth/token.ts` 负责读取、写入、清除 token。
- 所有普通 HTTP 请求继续走 `request()`，请求层自动补 `Authorization`。
- SSE 对话发送单独使用 `fetch`，也必须显式补 `Authorization`。
- 当前用户通过 React Query 缓存 `/auth/me` 结果，Header 和守卫共享同一 query key。

## 3. 页面交互

登录页字段：

- 账号：用户名或邮箱。
- 密码：密码输入框。
- 登录按钮：提交中展示 loading。

Header：

- 展示真实用户名和邮箱。
- 退出登录时清除 token、清除 auth query，并跳转 `/login`。

## 4. 权限展示

当前阶段普通用户和管理员开放相同功能，因此侧边栏不按角色隐藏菜单。后续如引入 RBAC，应优先在路由配置上声明权限，再由导航和守卫共用同一份规则。
