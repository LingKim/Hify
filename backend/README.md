# Hify Backend

## 本地初始账号

登录模块复用本地 `root` 管理员账号。开发环境初始化或重置该账号：

```bash
uv run python scripts/seed_root_user.py
```

默认登录信息：

- 用户名：`root`
- 密码：`123456`

该账号仅用于本地开发，生产环境部署后必须立即重置密码。
