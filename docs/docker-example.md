# Docker 部署示例

## 快速开始

### 1. 构建镜像

```bash
docker build -t lightrag-mcp .
```

### 2. 运行 MCP 服务器

```bash
# HTTP 模式 (单实例)
docker run --rm -p 8080:8080 \
  -e LIGHTRAG_BASE_URL=http://192.168.1.100:9621 \
  lightrag-mcp

# HTTP 模式 (多实例，共用端口)
docker run --rm -p 8080:8080 \
  -e LIGHTRAG_HTTP_PREFIXES=prefix1:http://localhost:9621:,prefix2:http://localhost:9622: \
  lightrag-mcp
```

### 3. 使用 Docker Compose

```bash
# 单实例
docker compose up lightrag-mcp -d

# 多实例 (共用 8080 端口)
docker compose up lightrag-mcp-multi -d
```

## 多实例部署 (Path 路由)

通过 `LIGHTRAG_HTTP_PREFIXES` 环境变量配置多个实例，共用同一端口：

```yaml
lightrag-mcp:
  image: lightrag-mcp
  command: ["daniel-lightrag-http", "--host", "0.0.0.0", "--port", "8080"]
  environment:
    # 格式: 前缀:URL:API密钥
    - LIGHTRAG_HTTP_PREFIXES=prefix1:http://lightrag:9621:,prefix2:http://lightrag:9622:
  ports:
    - "8080:8080"
```

**API 调用:**

```bash
# 前缀1 - 列出工具
curl http://localhost:8080/mcp/prefix1/tools

# 前缀1 - 执行查询
curl -X POST http://localhost:8080/mcp/prefix1/query_text \
  -H "Content-Type: application/json" \
  -d '{"query": "你的问题", "mode": "hybrid"}'

# 前缀2 - 执行查询
curl -X POST http://localhost:8080/mcp/prefix2/query_text \
  -H "Content-Type: application/json" \
  -d '{"query": "你的问题", "mode": "hybrid"}'
```

**效果:**
- 端口 8080 接收所有请求
- `/mcp/prefix1/*` → 连接 LightRAG:9621
- `/mcp/prefix2/*` → 连接 LightRAG:9622

## 环境变量

| 变量 | 说明 |
|------|------|
| `LIGHTRAG_BASE_URL` | 单实例模式: LightRAG 地址 |
| `LIGHTRAG_HTTP_PREFIXES` | 多实例模式: `prefix:url:key,...` |
| `LIGHTRAG_TIMEOUT` | 请求超时 (秒，默认 30) |
| `LIGHTRAG_TOOL_PREFIX` | 工具前缀 (可选) |
| `LIGHTRAG_HTTP_HOST` | HTTP 服务监听地址 (默认 127.0.0.1) |
| `LIGHTRAG_HTTP_PORT` | HTTP 服务端口 (默认 8080) |

## Claude Desktop 配置 (STDIO 模式)

```json
{
  "mcpServers": {
    "lightrag": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "lightrag-mcp"],
      "env": {
        "LIGHTRAG_BASE_URL": "http://localhost:9621"
      }
    }
  }
}
```

**Windows Docker Desktop**: 使用 `host.docker.internal` 替代 `localhost`
