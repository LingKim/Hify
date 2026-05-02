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

### 1.5 项目结构

```text
Hify/
├── CLAUDE.md          # 本文件 - 项目概述
├── backend/           # 后端服务（Python / FastAPI）
│   └── CLAUDE.md      # 后端完整开发规范
├── frontend/          # 前端应用（React / TypeScript）
│   └── CLAUDE.md      # 前端完整开发规范
├── docs/              # 项目文档
└── docker-compose.yml
```

## 2. 子项目规范

各子项目有独立的 CLAUDE.md，包含完整的开发规范和 AI 行为指令：

- **后端**：详见 [backend/CLAUDE.md](backend/CLAUDE.md)（模块架构、Python 编码规范、LLM 调用策略、数据模型、数据库规范、接口规范等）
- **前端**：详见 [frontend/CLAUDE.md](frontend/CLAUDE.md)（架构约定、目录规范、请求层、状态管理等）
