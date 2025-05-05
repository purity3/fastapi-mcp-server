# FastAPI MCP 服务器

FastAPI MCP服务器是一个基于FastAPI框架开发的Model Context Protocol (MCP) 集成应用，提供高性能的服务器端事件(SSE)通信和会话管理功能。

## 项目简介

此项目是一个轻量级的MCP服务器实现，主要用于模型上下文协议的交互。它采用FastAPI作为Web框架，支持异步请求处理，并通过会话管理实现多用户场景下的隔离。

## 核心功能

- **MCP集成**：完全支持Model Context Protocol，允许模型和客户端之间进行结构化通信
- **SSE传输**：使用服务器发送事件(Server-Sent Events)实现实时、低延迟的单向通信
- **会话管理**：支持多用户会话创建、存储和管理
- **认证系统**：提供基于token的API认证机制
- **异步处理**：全异步架构，确保高并发性能
- **工具注册**：支持注册自定义工具函数，扩展模型能力

## 项目结构

```
fastapi-mcp-server/
├── auth/               # 认证相关模块
├── database/           # 数据库连接和管理
├── models/             # 数据模型定义
├── routes/             # API路由定义
├── services/           # 业务逻辑服务
├── tools/              # 工具函数
├── transport/          # 传输层实现
├── utils/              # 通用工具函数
├── config.py           # 配置文件
├── main.py             # 应用入口
└── server.py           # MCP服务器初始化
```

## 安装指南

### 前置条件

- Python 3.13+
- 支持异步的数据库(可选)

### 安装步骤

1. 克隆代码库：

```bash
git clone <repository-url>
cd fastapi-mcp-server
```

2. 创建并激活虚拟环境：

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或者
.venv\Scripts\activate     # Windows
```

3. 安装依赖：

```bash
pip install -e .
```

4. 配置环境变量：

创建`.env`文件，参考`.env.example`设置必要的环境变量。

## 使用指南

### 启动服务器

```bash
python -m main
# 或使用安装的入口点
start
```

服务器默认运行在 http://localhost:8000

### API端点

- `/api/v1/session` - 会话管理API
- `/api/mcp` - MCP通信端点

### 自定义工具

在`tools/`目录下添加您的自定义工具函数，并在`server.py`中注册：

```python
@mcp.tool()
def your_custom_tool():
    # 实现您的工具逻辑
    pass
```

## 环境变量

- `HOST` - 服务器主机 (默认: 127.0.0.1)
- `PORT` - 服务器端口 (默认: 8000)
- `DATABASE_URL` - 数据库连接地址 (可选)

## 开发和贡献

欢迎提交问题和贡献代码。请确保遵循代码风格指南并添加适当的测试。

## 许可证

[添加您的许可证信息]
