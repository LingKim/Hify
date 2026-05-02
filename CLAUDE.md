# Hify - AI Agent 开发平台

## 1. 项目概述

### 1.1 产品定位

Hify 是一个简化版的 AI Agent 开发平台，参考 Dify 的核心能力，面向团队内部使用。

- 部署方式：本地部署
- 目标用户：20-50 人同时在线
- 核心理念：**创建 Agent → 配置工具/知识 → 对话使用**

### 1.2 MVP 做什么

- **应用编排**：Agent 模式 + Chatbot 模式，用配置文件/表单替代可视化编辑器
- **工作流引擎**：LLM 节点、IF/ELSE 条件分支、HTTP Request 节点、代码执行节点、Prompt 变量
- **知识库 / RAG**：文档上传、文本切片、向量索引（PGVector）、检索测试
- **模型管理**：多模型接入（OpenAI + Claude + Gemini + Ollama）、模型参数配置
- **工具集成**：自定义工具（OpenAPI 导入），用户自行接入 API
- **发布与集成**：Web UI（对话界面）、API 接口（供其他内部系统集成）
- **可观测性**：对话日志
- **团队管理**：基础认证（账密）、简单权限（管理员 / 普通用户）
- **部署**：Docker Compose 一键本地部署

### 1.3 MVP 不做什么

- 插件市场 / Marketplace
- MCP 协议集成
- 可视化 Workflow / Chatflow 编辑器（V2 延后）
- 嵌入式 Widget / iframe
- 前端模板定制、DSL 导入/导出
- 外部可观测平台对接（LangSmith / Langfuse）
- SSO / 审计日志 / 多租户
- 第一方工具封装（DALL-E、Wolfram 等）
- Iteration 循环节点、Template 模板节点

### 1.4 技术栈

- **后端**：Python 3.12 + FastAPI + SQLAlchemy + Alembic
- **AI**：LangChain（Agent 编排）+ PGVector（向量存储）+ tiktoken
- **前端**：React 18 + TypeScript + React Flow + Ant Design
- **缓存**：Redis（Agent 配置缓存 / Embedding 缓存 / 会话上下文缓存）
- **部署**：Docker Compose

## 2. 模块架构

### 2.1 目录结构

```text
hify/
├── app/
│   ├── main.py
│   ├── agent/
│   ├── conversation/
│   ├── knowledge/
│   ├── tool/
│   ├── llm/
│   ├── auth/
│   └── core/
├── alembic/
├── tests/
└── docker-compose.yml
```

### 2.2 模块职责

- `app/main.py`：FastAPI 入口，挂载各模块路由
- `app/agent/`：Agent 管理（CRUD + 配置）
- `app/conversation/`：对话引擎（SSE + Agent 执行器）
- `app/knowledge/`：知识库 / RAG（切片 + 向量化 + 检索）
- `app/tool/`：工具管理（OpenAPI 导入 + HTTP 执行）
- `app/llm/`：LLM 统一调用层（多提供商适配 + 限流 + 缓存 + 熔断）
- `app/auth/`：认证与权限（账密 + JWT）
- `app/core/`：共享基础设施（database / redis / config / deps）

### 2.3 模块依赖（4 层，严格单向）

```text
Layer 4  conversation -> agent, llm, knowledge, tool, core
Layer 3  agent -> core
Layer 2  knowledge -> llm, core
Layer 1  auth / llm / tool -> core
Layer 0  core -> 无
```

### 2.4 防循环依赖规则（强制）

1. `core` 不 import 任何业务模块。
2. `agent` 只存 ID 引用（`knowledge_base_id`、`tool_ids`、`llm_model_id`），存在性校验直接查 DB。
3. `tool` 是纯执行器，只做 HTTP 调用并返回原始结果，不调用 `llm`。
4. `knowledge` 单向调用 `llm`，仅用于 embedding，自行处理异常和回滚。
5. `conversation` 是唯一编排层，Agent 测试运行也放在这里。
6. 模块间只通过 `service` 层 async 函数通信，不直接 import 其他模块的 `model` 或 `router`。

### 2.5 Conversation 执行流程

用户发消息 → 加载 Agent 配置 → RAG 检索（如绑定知识库）→ 调用 LLM（SSE 流式）→ 执行工具（如 LLM 决定调工具）→ 结果回喂 LLM → 保存对话记录

---

## 3. 代码组织规范

### 3.1 模块内部文件结构（强制）

| 文件 | 职责 | 允许 import |
|---|---|---|
| `router.py` | HTTP 路由定义，处理请求协议、SSE、文件上传等 | `core`、同模块 `schema` + `service` |
| `schema.py` | Pydantic 请求/响应模型与字段校验 | 无业务模块 import |
| `service.py` | 业务逻辑核心，负责 DB、缓存、跨模块调用 | `core`、同模块 `model` + `schema`、其他模块 `service` |
| `model.py` | SQLAlchemy ORM 表定义 | `core.database.Base` + SQLAlchemy |
| `__init__.py` | 只导出 service 类，作为模块唯一对外入口 | 同模块 `service` |

### 3.2 各层禁止事项

- `router`：不写业务逻辑，不直接操作数据库，不 import 其他业务模块
- `schema`：不写业务方法，不依赖其他模块
- `model`：不写查询方法，不 import 其他模块 model
- `service`：不处理 HTTP 状态码、SSE 格式、文件响应等协议细节

### 3.3 跨模块调用规则

1. 通过 service 构造函数注入，示例：`self.agent_svc = AgentService(db)`
2. 不使用 FastAPI `Depends` 进行 service 之间的注入
3. 不使用全局 service 单例
4. 跨模块只传 Python 原生类型、`dict` 或当前模块 schema；不传 ORM 对象
5. 不 import 对方 schema 作为输入输出契约
6. 所有 service 方法默认 `async`
7. 同一请求内所有 service 共享同一个 Session，由 router 层注入

### 3.4 文件大小红线

- `router.py` <= 150 行
- `schema.py` <= 200 行
- `service.py` <= 400 行
- `model.py` <= 200 行

超过红线时，优先拆分职责，而不是继续堆叠分支逻辑。

### 3.5 命名规范

- 路由函数：`动词_名词`，例如 `create_agent`、`list_agents`
- Schema：`{Entity}{Action}`，例如 `AgentCreate`、`AgentDetail`
- Service 类：`{Entity}Service`
- Model 类：`{Entity}`
- 表名：蛇形复数，例如 `agents`、`knowledge_bases`

---

## 4. Python 编码规范

本节以 **Google Python Style Guide** 为基础，并结合本项目的 FastAPI / SQLAlchemy 场景固化为 AI 可直接执行的规则。

### 4.1 总体原则

1. 代码首先追求**可读性**，其次才是“聪明”。
2. 一个函数只做一件事；一个模块只承担一类职责。
3. 优先写直白代码，不为减少几行代码牺牲可维护性。
4. 任何“技巧型写法”如果需要额外解释，默认不用。

### 4.2 行宽与格式

- 默认行宽上限 `80` 字符。
- 仅以下情况允许超出 80：
  - 无法自然换行的 URL
  - import 路径或长常量名在换行后反而更难读
  - 框架强约束的字符串
- 使用 4 个空格缩进，禁止 Tab。
- 行尾不留多余空格。
- 文件结尾保留一个换行。
- 运算符两侧、逗号后、冒号后保持一个空格。

### 4.3 导入规范

- 使用**绝对导入**，除非包内相对导入明显更清晰。
- 禁止 `from x import *`。
- 每行只写一个 import。
- 导入顺序固定为三组，中间空一行：
  1. 标准库
  2. 第三方库
  3. 本项目模块
- 同组内按字母序排序。
- 若仅用于类型注解且可能引起循环依赖，使用：

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.agent.service import AgentService
```

### 4.4 命名规范

- 文件名、模块名：`snake_case`
- 变量名、函数名：`snake_case`
- 类名、异常名、Pydantic Schema 名：`PascalCase`
- 常量名：`UPPER_SNAKE_CASE`
- 私有属性或内部辅助函数：前缀 `_`
- 布尔变量必须可读为判断语义，例如 `is_active`、`has_error`、`can_retry`
- 禁止无语义缩写，以下场景除外：
  - 行业通用缩写：`id`、`url`、`http`、`llm`
  - 数学循环中的短变量：`i`、`j`

### 4.5 注释与 Docstring

- 注释只解释“为什么”，不解释肉眼可见的“做了什么”。
- 公共模块、公共类、公共函数必须写 docstring。
- 私有函数在逻辑简单时可以不写 docstring。
- docstring 使用三引号，首行写一句完整摘要。
- 多行 docstring 按以下顺序写：摘要、空行、详细说明、`Args`、`Returns`、`Raises`。
- 参数类型写在类型注解中，docstring 不重复堆叠类型解释，重点写业务含义和约束。


### 4.6 类型注解

- 新增或修改的 Python 代码默认补全类型注解。
- 所有公共函数、service 方法、工具函数都要标注参数和返回值。
- 不使用裸 `dict`、`list`、`tuple`，写成 `dict[str, Any]`、`list[str]` 这类具体形式。
- 可以返回 `None` 时显式写 `X | None`。
- 不把类型注解当注释摆设；如果类型不清晰，先重构接口再标注。
- 当返回结构稳定时，优先使用 Pydantic schema、`TypedDict` 或 dataclass，而不是匿名 `dict`。

### 4.7 函数设计

- 单个函数推荐控制在 40 行以内；超过 60 行必须评估拆分。
- 函数参数超过 5 个时，优先考虑 schema、dataclass 或配置对象。
- 不使用可变对象作为默认参数，例如：

```python
def bad(items: list[str] = []): ...
```

应写为：

```python
def good(items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    return items
```

- 简单判断直接返回，不写多余 `else`。
- 遇到非法输入或前置条件不满足时优先早返回，减少嵌套层级。

### 4.8 表达式与控制流

- `None` 比较必须使用 `is` / `is not`。
- 布尔判断直接写 `if is_ready:`，不要写 `if is_ready is True:`。
- 空容器判断直接写 `if not items:`，除非必须区分 `None` 和空容器。
- 列表推导式只用于简单映射或过滤；一旦出现多层嵌套或复杂条件，改成普通循环。
- 生成器表达式适用于一次性消费，不要为了“高级”滥用。
- 禁止把过多业务逻辑塞进单行表达式。

### 4.9 异常处理

- 只捕获你能处理的异常。
- 禁止裸 `except:`。
- 优先捕获明确异常类型，例如 `httpx.TimeoutException`、`IntegrityError`。
- 捕获后必须做一件有意义的事：
  - 转换为项目业务异常
  - 记录日志
  - 清理资源
  - 回滚事务
- 不要静默吞异常。
- 如果需要重新抛出，保留原始异常链：

```python
except IntegrityError as exc:
    await self.db.rollback()
    raise ValueError("Agent name already exists") from exc
```

### 4.10 日志规范

- 使用 `logging`，不要在业务代码里写 `print()`。
- 日志级别语义固定：
  - `debug`：开发排查细节
  - `info`：关键流程节点
  - `warning`：可恢复异常、重试、降级
  - `error`：当前请求失败
  - `exception`：伴随异常栈的错误
- 日志消息要包含可检索上下文，例如 `agent_id`、`provider_name`、`conversation_id`。
- 日志格式使用参数占位，不提前格式化字符串：

```python
logger.warning("Provider rate limited: provider=%s retry_after=%s", provider, retry_after)
```

### 4.11 字符串与常量

- 项目默认统一使用双引号 `"`.
- 优先使用 f-string 组织普通字符串。
- **日志**中不用 f-string，使用 logging 占位参数，避免无意义格式化开销。
- 用户可见文案、错误消息、配置 key、状态值不要散落硬编码；重复出现两次以上就提炼为常量或集中管理。

### 4.12 集合与数据结构

- 需要唯一性时使用 `set`，不要先用 `list` 再手动去重。
- 需要按键访问时使用 `dict`，不要用隐式位置元组表达业务数据。
- 跨层稳定返回结构优先 schema；临时内部组合数据才用 `dict`。
- 不为了“轻量”牺牲可读性，例如用 `tuple[0]`、`tuple[1]` 表达业务字段。

### 4.13 面向对象与抽象

- 只有当多个调用方共享同一职责时才抽象成基类或公共组件。
- 没有第二个真实实现前，不预建复杂接口层。
- Service 类可以存在，但不要继续套 Repository / Manager / Handler 多层空壳。
- 继承优先级低于组合；如果只是复用少量逻辑，优先提取函数。

### 4.14 FastAPI / Pydantic 约束

- `router.py` 只处理 HTTP 协议问题，不内联业务逻辑。
- 请求体、响应体必须通过 schema 明确声明。
- 所有查询参数、路径参数、请求体校验优先交给 Pydantic，不手写散乱校验。
- 路由函数保持薄，最多做：
  - 参数接收
  - 鉴权依赖
  - 调用 service
  - 返回统一响应

### 4.15 SQLAlchemy / 数据访问约束

- ORM model 只定义字段、约束、关系，不写业务逻辑。
- 查询、写入、事务控制统一放 `service.py`。
- 写操作涉及多步时，显式处理提交和回滚。
- 不跨模块传 ORM 实例，避免隐式懒加载和边界污染。
- 查询时禁止无条件 `SELECT *` 风格读取所有字段；按场景选择需要的数据。

### 4.16 异步编程约束

- I/O 相关路径默认使用 async 版本库和 async 接口。
- 禁止在 async 路径中直接调用阻塞 I/O。
- CPU 密集任务用 `asyncio.to_thread()` 或后台任务隔离。
- 外部调用必须显式设置超时，不能依赖第三方默认值。
- 遇到并发共享资源时，优先从设计上消除共享，而不是先上锁。

### 4.17 测试约束

- 新增业务逻辑时，至少覆盖：
  - 正常路径
  - 关键失败路径
  - 一个边界条件
- 测试命名使用 `test_<behavior>_<expected_result>`
- 测试只验证一个明确行为，避免一个测试覆盖过多分支
- 能在 service 层验证的逻辑，优先写 service 测试，不把所有测试都堆到 API 层

---

## 5. LLM 调用策略

### 5.1 协程管理

- 全程 async，使用各 SDK 的 async 接口，零阻塞
- CPU 密集操作（如 `tiktoken`）用 `asyncio.to_thread`
- 每个 Provider 复用一个 `httpx.AsyncClient` 连接池
- SSE 推送时必须检测客户端断连（`request.is_disconnected()`）

### 5.2 超时（三层）

- 连接超时：5s（Ollama 本地 3s）
- 首 Token 超时：60s（Ollama 120s）
- 总超时：300s（Ollama 600s）

### 5.3 重试

- 仅首 token 到达前的失败可重试：连接失败、429、5xx、超时
- 首 token 已发出后流中断，不重试
- 4xx 客户端错误（例如 401）不重试
- 采用指数退避 + 随机抖动，最多 3 次
- 429 时优先使用 `Retry-After`

### 5.4 容错

- 每个 Provider 独立熔断
- 连续 5 次失败后打开熔断，冷却 30s 后探测
- 主 Provider 失败后按 Fallback 链自动切换
- 统一 provider 适配接口，屏蔽 OpenAI / Claude / Gemini / Ollama 差异

---

## 6. 部署架构

### 6.1 部署组成

- Nginx：反向代理与静态资源托管
- FastAPI：业务服务入口
- PostgreSQL + PGVector：业务数据与向量检索
- Redis：缓存、限流计数、SSE 上下文
- Ollama（可选）：本地模型推理

### 6.2 部署原则

- 所有外部流量统一经 Nginx 进入
- SSE 路径关闭 `proxy_buffering`，超时设为 600s，并在每次 `yield` 前检测客户端断连
- 文档上传与 Embedding 处理异步化，接口立即返回 `task_id`
- PostgreSQL 使用 async 连接池，向量列建 HNSW 索引
- LLM 调用链必须具备限流、重试、Fallback 和熔断能力

---


## 7. 缓存策略

### 7.1 Redis 职责

- Agent 配置热缓存：write-through，变更时主动失效
- Embedding 结果缓存：相同文本不重复调模型，设置 TTL
- LLM API 限流计数：滑动窗口
- SSE 上下文临时存储：支持断连重连恢复

### 7.2 缓存原则

- 缓存数据全部可从 PostgreSQL 重建
- Phase 0-1 可不持久化，Phase 1 后开启 AOF
- Agent 配置变更时主动失效，不靠 TTL 被动过期
- 限流计数按 Provider 分开统计

### 7.3 不缓存的内容

- 对话消息：直接写 PostgreSQL
- 用户认证：JWT 无状态，不走缓存
- 工具执行结果：实时调用外部 API，不缓存

---

## 8. 数据模型

### 8.1 核心表（12 张）

| 表 | 职责 | 级别 |
|---|---|---|
| users | 用户账号，含角色 | 冷表 |
| llm_providers | LLM 供应商凭据（API Key、端点） | 冷表 |
| llm_models | 模型配置（参数），绑定 provider | 冷表 |
| knowledge_bases | 知识库，归属用户 | 冷表 |
| documents | 上传的原始文档，归属知识库 | 冷表 |
| document_chunks | 切片 + 向量，归属文档 | 温表 |
| tools | 工具定义（OpenAPI Schema），归属用户 | 冷表 |
| agents | Agent 配置，绑定模型和知识库 | 冷表 |
| agent_tools | Agent 与工具多对多关联 | 冷表 |
| conversations | 对话会话，关联用户和 Agent | 冷表 |
| messages | 消息记录，关联对话 | 热表 |
| message_citations | 消息与切片多对多关联（RAG 引用溯源） | 热表 |

### 8.2 核心关系

- `users` 1:N `agents`、`knowledge_bases`、`tools`、`conversations`
- `agents` N:1 `llm_models`
- `agents` N:1 `knowledge_bases`（可空）
- `agents` N:M `tools`（通过 `agent_tools`）
- `llm_providers` 1:N `llm_models`
- `knowledge_bases` 1:N `documents`
- `documents` 1:N `document_chunks`
- `conversations` N:1 `agents`、N:1 `users`
- `conversations` 1:N `messages`
- `messages` N:M `document_chunks`（通过 `message_citations`）

### 8.3 设计决策

- `llm_providers` 与 `llm_models` 分开，便于多个模型共享同一凭据
- `agents` 与 `knowledge_bases` 当前采用 N:1，后续多知识库再扩展关联表
- `message_citations` 独立建表，支持 RAG 引用溯源

---

## 9. 数据库规范

### 9.1 索引原则

- 主键统一 `BIGINT` 自增，不用 UUID
- 外键字段必须单独建索引，除非已被复合索引左前缀覆盖
- 复合索引按区分度降序排列
- 向量列必须建 HNSW 索引
- 唯一约束配合 `WHERE deleted_at IS NULL` 排除软删除行
- 高频状态过滤查询优先考虑部分索引

### 9.2 大表应对

- 热表（`messages`、`message_citations`）在 Phase 2 启用按月 RANGE 分区
- 删除历史数据通过 `DROP PARTITION`
- `document_chunks` 暂不分区，优先保证向量索引和文档维度检索效率

### 9.3 分页原则

- 热表必须使用游标分页（keyset pagination），禁止 OFFSET
- 冷表可以使用 OFFSET
- 总量超过 1 万行的表优先用游标分页
- 分页查询禁止 `SELECT *`

### 9.4 通用字段约定

- 每张表必须包含：
  - `id`：`BIGINT` 自增
  - `created_at`：`TIMESTAMPTZ`
  - `updated_at`：`TIMESTAMPTZ`
  - `deleted_at`：`TIMESTAMPTZ`
- 时间字段统一 `TIMESTAMPTZ`
- 状态字段用 `VARCHAR + CHECK`，不用 ENUM
- 短字符串用 `VARCHAR(n)` 且长度明确
- 长文本用 `TEXT`
- 灵活扩展字段用 `JSONB`
- 布尔字段用 `BOOLEAN NOT NULL DEFAULT FALSE`

---

## 10. 接口规范

### 10.1 路径规范

统一采用 RESTful 风格：`/api/v1/{resource_plural}`

```text
GET    /api/v1/providers
POST   /api/v1/providers
GET    /api/v1/providers/{id}
PUT    /api/v1/providers/{id}
DELETE /api/v1/providers/{id}
POST   /api/v1/providers/{id}/test-connection
```

### 10.2 统一响应

所有接口统一返回 `Result<T>`：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

### 10.3 分页

- 请求参数：`page`（从 1 开始）、`pageSize`（默认 20，最大 100）
- 响应结构：`Result<PageResult<T>>`
- `PageResult` 至少包含：`list`、`total`、`page`、`pageSize`

### 10.4 空值约定

- 列表字段空时返回 `[]`
- 字符串字段空时返回 `""`
- 对象不存在时返回 `null`

### 10.5 错误码

HTTP 状态码照常返回，`code` 字段用于业务级细分。

| 范围 | 模块 | 常见错误码 |
|---|---|---|
| 1xxx | 通用 | 1000 未知错误、1001 参数校验失败、1002 资源不存在、1003 资源已存在、1004 操作过于频繁 |
| 2xxx | auth | 2001 用户名或密码错误、2002 Token 过期、2003 Token 无效、2004 权限不足、2005 账户已禁用 |
| 3xxx | llm | 3001 模型不存在、3002 Provider 连接失败、3003 Provider 认证失败、3004 请求超时、3005 上游限流、3006 所有 Provider 不可用、3007 模型参数无效 |
| 4xxx | agent | 4001 Agent 不存在、4002 配置无效、4003 绑定的模型不存在、4004 绑定的知识库不存在、4005 绑定的工具不存在 |
| 5xxx | knowledge | 5001 知识库不存在、5002 文档不存在、5003 文档格式不支持、5004 文件大小超限、5005 文档处理失败、5006 文档处理中、5007 向量检索失败 |
| 6xxx | tool | 6001 工具不存在、6002 OpenAPI Schema 无效、6003 工具执行失败、6004 工具执行超时 |
| 7xxx | conversation | 7001 对话不存在、7002 Agent 未配置模型、7003 SSE 连接异常、7004 消息内容为空、7005 对话已关闭 |

细分规则：

- `x000-x099`：通用错误
- `x100-x199`：核心业务错误
- `x200-x299`：外部依赖错误
- `x300-x999`：预留扩展

新增错误码只能在所属模块范围内追加，不能跨模块占用。

---

## 11. AI 行为指令

### 11.1 写代码时

- 先阅读相关模块，再开始修改；不要凭印象写代码
- 每个功能先用最简单直接的方式实现
- 不引入不必要的设计模式
- 不做过度抽象
- 不新增技术栈之外的依赖；确实需要时，先说明原因再等确认
- 所有外部调用必须显式设置超时
- 配置项统一外化，不硬编码到业务代码
- 修改现有代码时，优先保持接口契约稳定

### 11.2 改代码时

- 先确认本次改动落在哪个模块边界内
- 不要为了一个小需求顺手重构无关模块
- 不要把 service 逻辑塞进 router
- 不要把 HTTP、数据库、缓存、LLM 调用耦合到同一个函数
- 如果发现现有设计与需求冲突，先指出冲突点，再给出 2-3 个可选方案

### 11.3 写数据库相关代码时

- 先确认表关系、索引、分页策略是否受影响
- 新增字段默认考虑：是否需要 `NOT NULL`、默认值、索引、软删除兼容
- 新增查询默认考虑：是否命中索引、是否会扫大表、是否需要游标分页
- 不因为“写起来方便”跳过约束设计

### 11.4 写接口时

- 先定义 schema，再写 router 和 service
- 保持统一响应结构
- 非 CRUD 行为用明确动词路径
- 错误码必须落到已有模块范围内

### 11.5 写异步和外部调用时

- 默认考虑超时、重试、取消、断连、日志
- 对上游失败要给出可观测信息，不要只返回 “failed”
- SSE 相关路径默认考虑客户端提前断开

### 11.6 不确定时

- 架构和模型层面的不确定问题，先给 2-3 个方案对比，再等待拍板
- 如果规范没有覆盖，先遵循“简单、稳定、可维护”原则
- 如果用户前提本身有问题，要直接指出，不要顺着错误前提继续做

### 11.7 明确禁止

- 禁止无理由引入新依赖
- 禁止跨模块直接 import 对方 model 或 router
- 禁止在 `schema.py` 写业务逻辑
- 禁止在 `model.py` 写查询逻辑
- 禁止在 `router.py` 写数据库操作
- 禁止吞异常不处理
- 禁止阻塞式 I/O 混入 async 主路径
- 禁止为了“以后可能会用”预埋复杂抽象

---
