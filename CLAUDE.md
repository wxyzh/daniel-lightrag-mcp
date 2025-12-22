# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 LightRAG 的 MCP (Model Context Protocol) 服务器，提供了完整的功能集成，包含 22 个可用工具，分为 4 个主要类别：
- 文档管理 (7 个工具)
- 查询操作 (2 个工具，支持 5 种模式和 11 个高级参数)
- 知识图谱 (9 个工具，完整的 CRUD 支持)
- 系统管理 (4 个工具，包括健康检查)

## 常用开发命令

### 安装和设置
```bash
# 安装项目
pip install -e .

# 安装开发依赖
pip install -e ".[dev]"

# 启动 MCP 服务器
daniel-lightrag-mcp

# 或者使用 Python 模块方式
python -m daniel_lightrag_mcp
```

### 测试和代码质量
```bash
# 运行测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=src/daniel_lightrag_mcp --cov-report=html

# 格式化代码
black src/ tests/
isort src/ tests/

# 类型检查
mypy src/
```

### 开发环境配置
```bash
# 设置开发环境变量
export LIGHTRAG_BASE_URL="http://localhost:9621"
export LIGHTRAG_API_KEY="your-api-key"  # 可选
export LIGHTRAG_TIMEOUT="30"            # 可选
export LOG_LEVEL="INFO"                 # 可选

# 启动调试模式
export LOG_LEVEL=DEBUG
python -m daniel_lightrag_mcp
```

## 架构和代码结构

### 核心架构
- **MCP 服务器模式**: 使用标准的 MCP 协议与客户端通信
- **异步客户端**: 基于 httpx 的异步 HTTP 客户端与 LightRAG API 交互
- **Pydantic 模型**: 严格的类型验证和序列化/反序列化
- **分层错误处理**: 自定义异常层次结构，提供详细的错误信息

### 主要模块

#### `src/daniel_lightrag_mcp/server.py`
- MCP 服务器的核心实现
- 包含 22 个工具的处理逻辑
- 详细的日志记录和错误处理
- 工具参数验证和响应格式化

#### `src/daniel_lightrag_mcp/client.py`
- LightRAG API 的异步客户端
- 所有 API 调用的封装
- HTTP 错误映射和重试逻辑
- 连接管理和资源清理

#### `src/daniel_lightrag_mcp/models.py`
- Pydantic 模型定义
- 请求/响应数据验证
- 枚举类型定义
- 数据序列化/反序列化

#### `src/daniel_lightrag_mcp/cli.py`
- 命令行入口点
- 异常处理和优雅关闭

### 工具分类和功能

#### 文档管理工具
- `insert_text`: 插入单个文本文档
- `insert_texts`: 批量插入文本文档
- `upload_document`: 上传文件文档
- `scan_documents`: 扫描新文档
- `get_documents`: 获取所有文档
- `get_documents_paginated`: 分页获取文档
- `delete_document`: 删除指定文档

#### 查询工具
- `query_text`: 文本查询
  - **5 种查询模式**: naive (简单向量搜索), local (实体聚焦检索), global (社区摘要), hybrid (组合 local+global), mix (知识图谱+向量检索)
  - **11 个高级参数**:
    - 检索控制: `top_k`, `max_entity_tokens`, `max_relation_tokens`
    - 引用和内容: `include_references`, `include_chunk_content`
    - 重排序: `enable_rerank`
    - 多轮对话: `conversation_history`
    - 输出控制: `only_need_context`, `only_need_prompt`, `stream`
- `query_text_stream`: 流式文本查询（支持所有上述模式和参数）

#### 知识图谱工具（完整的 CRUD 支持）
- `get_knowledge_graph`: 获取知识图谱
- `get_graph_labels`: 获取图标签
- `check_entity_exists`: 检查实体是否存在
- **`create_entity`**: 创建新实体（需要 entity_name 和 properties）
- `update_entity`: 更新实体属性
- `delete_entity`: 删除实体
- **`create_relation`**: 创建新关系（需要 source_entity, target_entity 和 properties）
- `update_relation`: 更新关系属性
- `delete_relation`: 删除关系

#### 系统管理工具
- `get_pipeline_status`: 获取管道状态
- `get_track_status`: 获取跟踪状态
- `get_document_status_counts`: 获取文档状态统计
- `get_health`: 健康检查

### 最新功能增强 (v0.2.0)

#### 查询功能增强
- **新增 mix 查询模式**: 结合知识图谱和向量检索，提供最全面的检索能力
- **11 个高级查询参数**:
  - `top_k`: 控制检索结果数量
  - `max_entity_tokens`: Local 模式的实体令牌上限
  - `max_relation_tokens`: Global 模式的关系令牌上限
  - `include_references`: 在响应中包含引用信息
  - `include_chunk_content`: 在引用中包含块内容（需要 include_references=true）
  - `enable_rerank`: 启用重排序提升检索质量
  - `conversation_history`: 多轮对话历史（List[Dict[str, str]]）
  - `only_need_context`: 仅返回上下文不生成
  - `only_need_prompt`: 仅返回提示词
  - `stream`: 流式返回结果

#### 知识图谱 CRUD 完整性
- **新增 create_entity**: 完整支持实体创建，需要提供 entity_name 和 properties
- **新增 create_relation**: 完整支持关系创建，需要提供 source_entity, target_entity 和 properties
- **API 端点对齐**: 删除操作使用官方 API 路径
  - 实体删除: `/rag/delete_by_entity`
  - 关系删除: `/rag/delete_by_relation`

#### 查询模式详细说明
1. **naive**: 简单向量搜索，最快但最基础
2. **local**: 实体聚焦检索，适合局部细节查询
3. **global**: 社区摘要，适合全局概览查询
4. **hybrid**: 结合 local 和 global，平衡细节和全局
5. **mix**: 知识图谱 + 向量检索，最全面的检索模式

### 错误处理模式
项目使用分层的异常处理体系：
- `LightRAGError`: 基础异常类
- `LightRAGConnectionError`: 连接错误
- `LightRAGAuthError`: 认证错误
- `LightRAGValidationError`: 验证错误
- `LightRAGAPIError`: API 错误
- `LightRAGTimeoutError`: 超时错误
- `LightRAGServerError`: 服务器错误

### 日志记录
- 使用结构化日志格式
- 详细的工具执行跟踪
- 错误上下文信息记录
- 可配置的日志级别

## 开发注意事项

### 添加新工具
1. 在 `server.py` 中的 `handle_list_tools()` 函数中添加工具定义
2. 在 `handle_call_tool()` 函数中添加工具处理逻辑
3. 在 `client.py` 中添加对应的客户端方法
4. 在 `models.py` 中添加必要的请求/响应模型
5. 更新工具计数和验证逻辑

### 测试
- 使用 `pytest` 进行单元测试
- 使用 `pytest-asyncio` 进行异步测试
- 使用 `pytest-mock` 进行模拟测试
- 集成测试在 `test_integration.py` 中

### 代码风格
- 使用 `black` 进行代码格式化（行长度 88 字符）
- 使用 `isort` 进行导入排序
- 使用 `mypy` 进行类型检查
- 遵循异步/等待模式

### 环境变量
- `LIGHTRAG_BASE_URL`: LightRAG 服务器地址（默认: http://localhost:9621）
- `LIGHTRAG_API_KEY`: API 密钥（可选）
- `LIGHTRAG_TIMEOUT`: 请求超时时间（默认: 30 秒）
- `LOG_LEVEL`: 日志级别（默认: INFO）
- `LIGHTRAG_TOOL_PREFIX`: 工具名称前缀（可选，用于运行多个 MCP 实例）

### 多实例部署（工具前缀）

如果你需要同时运行多个 LightRAG MCP 服务器实例（例如，一个用于小说风格查询，另一个用于正文查询），可以使用 `LIGHTRAG_TOOL_PREFIX` 环境变量来区分不同实例的工具。

**使用示例：**

```bash
# 实例1：小说风格查询
export LIGHTRAG_BASE_URL="http://localhost:9621"
export LIGHTRAG_TOOL_PREFIX="novel_style_"
python -m daniel_lightrag_mcp

# 实例2：小说正文查询
export LIGHTRAG_BASE_URL="http://localhost:9622"
export LIGHTRAG_TOOL_PREFIX="novel_content_"
python -m daniel_lightrag_mcp
```

**效果：**
- 工具名称会自动添加前缀：
  - 实例1: `novel_style_query_text`, `novel_style_insert_text`, ...
  - 实例2: `novel_content_query_text`, `novel_content_insert_text`, ...
- 工具描述会显示前缀标记：
  - `[novel_style] Query LightRAG with text`
  - `[novel_content] Query LightRAG with text`

这样你就可以在同一个 MCP 客户端中区分不同数据源的工具，避免混淆。

## 与 LightRAG 服务器的交互

此 MCP 服务器假定 LightRAG 服务器运行在 `http://localhost:9621`，并提供了完整的 API 覆盖。确保在使用此 MCP 服务器之前，LightRAG 服务器正在运行并且可访问。

### 典型工作流程
1. 使用 `get_health` 检查服务器状态
2. 使用 `insert_text` 或 `upload_document` 添加文档
3. 使用 `query_text` 进行查询（推荐使用 hybrid 或 mix 模式）
   - 使用 `include_references=true` 获取引用信息
   - 使用 `enable_rerank=true` 提升检索质量
   - 使用 `conversation_history` 进行多轮对话
4. 使用 `get_knowledge_graph` 探索知识图谱
5. 使用 `create_entity` 和 `create_relation` 手动构建知识
6. 使用系统管理工具监控状态

### 项目特性
- ✅ **100% 功能覆盖**: 所有 22 个工具完整实现并通过测试
- ✅ **完整的 CRUD 支持**: 知识图谱支持创建、读取、更新、删除操作
- ✅ **5 种查询模式**: 从简单向量搜索到知识图谱混合检索
- ✅ **11 个高级查询参数**: 精细控制检索行为和输出
- ✅ **多轮对话支持**: 通过 conversation_history 实现上下文感知查询
- ✅ **流式查询**: 支持实时流式返回查询结果
- ✅ **批量操作**: 支持批量插入和删除文档
- ✅ **分页查询**: 高效处理大量文档
- ✅ **多实例部署**: 通过工具前缀支持同时运行多个实例
- ✅ **详细日志**: 结构化日志记录，便于调试和监控