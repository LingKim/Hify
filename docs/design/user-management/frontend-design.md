# 用户管理前端文档

## 1. 页面目标

前端新增一个“用户管理”页面，用于维护 Hify 内部账号、角色和启用状态，替代界面和会话链路中依赖固定用户的方式。

## 2. 页面职责

页面职责：

- 查看用户列表
- 按关键词、角色、状态筛选
- 新增用户
- 编辑用户基础资料
- 启用或禁用用户
- 重置用户密码
- 软删除用户

## 3. 路由与领域结构

路由：

- `/users`

页面组件：

- `frontend/src/pages/user-management/UserManagementPage.tsx`

领域模块：

- `frontend/src/domain/user-management/api.ts`
- `frontend/src/domain/user-management/service.ts`
- `frontend/src/domain/user-management/queries.ts`
- `frontend/src/domain/user-management/types.ts`
- `frontend/src/domain/user-management/components.tsx`

## 4. 页面结构

页面采用现有共享组件：

- `ListTable`：承载列表、筛选、分页和行操作
- `FormDialog`：承载新增、编辑和重置密码弹窗

列表列：

- 用户名与邮箱
- 角色
- 状态
- 最后登录
- 创建时间
- 操作

筛选项：

- 关键词：匹配用户名和邮箱
- 角色：管理员、普通用户
- 状态：启用、禁用

## 5. 表单结构

新增用户：

- 用户名
- 邮箱
- 角色
- 状态
- 初始密码

编辑用户：

- 用户名
- 邮箱
- 角色
- 状态

重置密码：

- 新密码

## 6. 交互规则

- 删除和禁用使用二次确认。
- 重置密码独立弹窗，不和编辑资料混在一起。
- 操作列超过三个动作时由 `ListTable` 自动收纳为主操作和更多操作。
- 用户名、邮箱、角色和状态使用用户可理解文案，不暴露数据库字段。

## 7. 后续扩展

RBAC 上线后：

- 角色选项从后端接口读取。
- 用户列表可以展示多角色标签。
- 编辑表单可以从单选角色升级为多选角色。
- 权限管理可新增独立页面，不挤进用户基础资料表单。
