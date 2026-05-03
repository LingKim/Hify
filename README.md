# Hify

Hify 当前采用前后端分离结构：

- `backend/`：FastAPI 后端骨架
- `frontend/`：React 18 + TypeScript + Vite 8 前端骨架

## 本地开发

### 后端环境配置

后端启动前会按顺序自动读取这些文件中的环境变量：

- `backend/.env`
- `backend/.env.local`
- `backend/.env.development`
- `backend/.env.development.local`

本地开发建议先参考 `backend/.env.example`，当前仓库已经补了一个可直接用于本机 Docker PostgreSQL / Redis 的 `backend/.env.development`。

默认本地开发配置为：

- PostgreSQL：`postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/hify`
- Redis：`redis://127.0.0.1:6379/0`

### 一键启动

在仓库根目录执行：

```bash
make start
```

命令会完成以下动作：

1. 检查前端依赖是否已安装
2. 启动 FastAPI 开发服务
3. 启动 Vite 开发服务
4. 自动打开浏览器访问前端页面

默认地址：

- 前端：`http://127.0.0.1:5173`
- 后端：`http://127.0.0.1:8000`

如需覆盖端口，可在执行前设置环境变量：

```bash
FRONTEND_PORT=5174 BACKEND_PORT=8001 make start
```

### 常用命令

```bash
make start
make stop
make restart
make build
make clean
make package
```

说明：

1. `make stop`：停止当前后台运行的前后端服务
2. `make restart`：重启前后端服务
3. `make build`：构建后端分发产物与前端静态资源
4. `make clean`：清理构建产物、打包产物和运行日志
5. `make package`：先构建，再输出根目录 `dist/` 下的可分发 `tar.gz`

打包产物会包含：

1. 前端 `dist/` 静态资源
2. 后端 `wheel/sdist` 构建产物
3. 后端运行源码与基础元数据
4. 根目录说明文件与 `Makefile`
```

### 单独启动前端

```bash
cd frontend
pnpm install
pnpm dev
```

### 单独启动后端

```bash
cd backend
uv run alembic upgrade head
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 前端质量工具

```bash
cd frontend
pnpm lint
pnpm format:check
```

## 前端目录说明

前端采用混合式 DDD 结构：

- `src/app`：应用入口、路由、布局、Provider
- `src/shared`：共享基础设施，如请求层、环境配置、通用类型
- `src/domain`：领域模块，按业务名词组织
- `src/pages`：页面层，只负责组合与展示

当前示例领域为 `health`，用于验证前端到后端 `/api/v1/health` 的联调链路。
