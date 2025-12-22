# Streamable HTTP Server Guide

## Overview

The LightRAG MCP HTTP Server provides a REST API interface to access all MCP tools via HTTP with prefix-based routing and streaming support.

**Key Features:**
- 🚀 REST API for all 20+ MCP tools
- 🔀 Prefix-based routing for multiple instances
- 📡 Streaming HTTP responses (NDJSON format)
- 🔌 Completely separate from stdio MCP server
- ⚡ Async/await throughout
- 🎯 FastAPI-based with automatic API docs

## Installation

The HTTP server requires additional dependencies:

```bash
pip install -e ".[http]"
```

Or install directly:

```bash
pip install fastapi uvicorn
```

## Quick Start

### 1. Basic Usage (Single Instance)

The HTTP server can be started using the main command with the `--http` flag:

```bash
# Start HTTP server on default port (8765)
daniel-lightrag-mcp --http

# Or use the shortcut command
daniel-lightrag-http

# Or specify host and port
daniel-lightrag-mcp --http --host 0.0.0.0 --port 8080
```

**Note:** The `daniel-lightrag-http` command is a shortcut that automatically adds the `--http` flag.

**Default Configuration:**
- Host: `127.0.0.1` (localhost only, for security)
- Port: `8765`
- To allow external connections: use `--host 0.0.0.0`

### 2. Configure Multiple Instances

Set environment variable for multiple prefixes:

```bash
export LIGHTRAG_HTTP_PREFIXES="novel_style:http://localhost:9621:key1,novel_content:http://localhost:9622:key2"
daniel-lightrag-http
```

Format: `prefix:url:api_key,prefix2:url2:api_key2`

### 3. Test the Server

```bash
# Health check
curl http://localhost:8000/health

# List tools for a prefix
curl http://localhost:8000/mcp/novel_style/tools

# Execute a tool
curl -X POST http://localhost:8000/mcp/novel_style/novel_style_query_text \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "query": "What writing style is used?",
      "mode": "hybrid"
    }
  }'
```

## API Endpoints

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "prefixes": ["novel_style", "novel_content"],
  "version": "0.1.0"
}
```

### GET /mcp/{prefix}/tools

List all tools for a specific prefix.

**Parameters:**
- `prefix`: Tool prefix (e.g., "novel_style")

**Response:**
```json
{
  "prefix": "novel_style",
  "tools": [
    {
      "name": "novel_style_query_text",
      "description": "[novel_style] Query LightRAG with text",
      "input_schema": {
        "type": "object",
        "properties": {...},
        "required": [...]
      }
    },
    ...
  ],
  "count": 20
}
```

### POST /mcp/{prefix}/{tool_name}

Execute a tool.

**Parameters:**
- `prefix`: Tool prefix
- `tool_name`: Full tool name including prefix (e.g., "novel_style_query_text")

**Request Body:**
```json
{
  "arguments": {
    "query": "Your query here",
    "mode": "hybrid"
  },
  "stream": false
}
```

**Response (Regular):**
```json
{
  "success": true,
  "data": {
    "response": "...",
    "results": [...]
  }
}
```

**Response (Streaming):**

For streaming tools (or when `stream: true`), the response is NDJSON (Newline-Delimited JSON):

```
{"type":"chunk","data":"First chunk"}
{"type":"chunk","data":"Second chunk"}
{"type":"chunk","data":"Third chunk"}
{"type":"done","status":"completed"}
```

## Configuration

### Environment Variables

**Single Instance (Default):**
```bash
export LIGHTRAG_BASE_URL="http://localhost:9621"
export LIGHTRAG_API_KEY="your-api-key"
```

**HTTP Server Host and Port:**
```bash
# Host to bind (default: 0.0.0.0)
export LIGHTRAG_HTTP_HOST="0.0.0.0"

# Port to bind (default: 8000)
# Change this if port 8000 is already in use
export LIGHTRAG_HTTP_PORT="8080"
```

**Multiple Instances:**
```bash
export LIGHTRAG_HTTP_PREFIXES="prefix1:url1:key1,prefix2:url2:key2"
```

Example:
```bash
export LIGHTRAG_HTTP_PREFIXES="novel_style:http://localhost:9621:secret1,novel_content:http://localhost:9622:secret2,research:http://localhost:9623:secret3"
```

### Priority Order

Configuration is resolved in the following order:
1. **Command-line arguments** (highest priority)
2. **Environment variables**
3. **Default values** (lowest priority)

Example:
```bash
# Set default port via environment
export LIGHTRAG_HTTP_PORT=9000

# Override with command line
daniel-lightrag-http --port 8080  # Uses 8080, not 9000
```

### Server Options

```bash
daniel-lightrag-http --help
```

Options:
- `--host HOST` - Host to bind (default: 0.0.0.0)
- `--port PORT` - Port to bind (default: 8000)
- `--reload` - Enable auto-reload for development

## Usage Examples

### Example 1: Query Text

```python
import requests

response = requests.post(
    "http://localhost:8000/mcp/novel_style/novel_style_query_text",
    json={
        "arguments": {
            "query": "What writing techniques are used?",
            "mode": "hybrid"
        }
    }
)

result = response.json()
print(result['data']['response'])
```

### Example 2: Streaming Query

```python
import requests
import json

response = requests.post(
    "http://localhost:8000/mcp/novel_style/novel_style_query_text_stream",
    json={
        "arguments": {
            "query": "Explain the plot",
            "mode": "local"
        },
        "stream": true
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        data = json.loads(line)
        if data['type'] == 'chunk':
            print(data['data'], end='', flush=True)
        elif data['type'] == 'done':
            print("\nCompleted!")
        elif data['type'] == 'error':
            print(f"Error: {data['error']}")
```

### Example 3: Insert Document

```python
import requests

response = requests.post(
    "http://localhost:8000/mcp/novel_content/novel_content_insert_text",
    json={
        "arguments": {
            "text": "Chapter 15: The protagonist discovers the hidden truth..."
        }
    }
)

result = response.json()
print(f"Track ID: {result['data']['track_id']}")
```

### Example 4: Get Knowledge Graph

```python
import requests

response = requests.post(
    "http://localhost:8000/mcp/novel_style/novel_style_get_knowledge_graph",
    json={"arguments": {}}
)

result = response.json()
nodes = result['data']['nodes']
edges = result['data']['edges']

print(f"Nodes: {len(nodes)}, Edges: {len(edges)}")
```

## Client Libraries

### JavaScript/TypeScript

```typescript
import axios from 'axios';

const client = axios.create({
  baseURL: 'http://localhost:8000/mcp/novel_style',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Query
const response = await client.post('/novel_style_query_text', {
  arguments: {
    query: 'Your question',
    mode: 'hybrid'
  }
});

console.log(response.data.data.response);

// Streaming
const streamResponse = await client.post(
  '/novel_style_query_text_stream',
  {
    arguments: { query: 'Your question' },
    stream: true
  },
  { responseType: 'stream' }
);

for await (const chunk of streamResponse.data) {
  const line = chunk.toString();
  const data = JSON.parse(line);
  if (data.type === 'chunk') {
    process.stdout.write(data.data);
  }
}
```

### Python (with async)

```python
import aiohttp
import asyncio
import json

async def query_stream(prefix: str, query: str):
    url = f"http://localhost:8000/mcp/{prefix}/{prefix}_query_text_stream"

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url,
            json={
                "arguments": {"query": query},
                "stream": True
            }
        ) as response:
            async for line in response.content:
                if line:
                    data = json.loads(line)
                    if data['type'] == 'chunk':
                        print(data['data'], end='', flush=True)

asyncio.run(query_stream('novel_style', 'What is the main theme?'))
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY . .
RUN pip install -e .

EXPOSE 8000

CMD ["daniel-lightrag-http", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t lightrag-http .
docker run -p 8000:8000 \
  -e LIGHTRAG_HTTP_PREFIXES="..." \
  lightrag-http
```

### Nginx Proxy

```nginx
upstream lightrag_http {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://lightrag_http;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # For streaming
        proxy_buffering off;
        proxy_cache off;
    }
}
```

### systemd Service

Create `/etc/systemd/system/lightrag-http.service`:

```ini
[Unit]
Description=LightRAG MCP HTTP Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/lightrag-mcp
Environment="LIGHTRAG_HTTP_PREFIXES=..."
ExecStart=/usr/local/bin/daniel-lightrag-http --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable lightrag-http
sudo systemctl start lightrag-http
sudo systemctl status lightrag-http
```

## API Documentation

The HTTP server provides automatic API documentation via FastAPI:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Troubleshooting

### Server won't start

```bash
# Check if port is in use
lsof -i :8000

# Or use a different port
daniel-lightrag-http --port 8001
```

### Connection refused

```bash
# Verify LightRAG servers are running
curl http://localhost:9621/health
curl http://localhost:9622/health

# Check environment variables
echo $LIGHTRAG_HTTP_PREFIXES
```

### Streaming not working

- Ensure no buffering proxy in between
- Check `X-Accel-Buffering: no` header is set
- Verify client supports streaming responses

## Comparison: stdio vs HTTP

| Feature | stdio MCP | HTTP Server |
|---------|-----------|-------------|
| Protocol | stdio | HTTP/REST |
| Client | Claude Desktop, IDE | Any HTTP client |
| Streaming | Built-in | NDJSON |
| Multiple instances | Config-based | Environment vars |
| Remote access | No | Yes |
| Load balancing | No | Yes (via proxy) |
| Browser access | No | Yes |

## Best Practices

1. **Use prefixes for isolation** - Different databases need different prefixes
2. **Enable CORS for web clients** - Add CORS middleware if needed
3. **Secure with API keys** - Add authentication middleware
4. **Monitor with health endpoint** - Set up monitoring for `/health`
5. **Use nginx for production** - Proxy and load balance
6. **Log to files** - Configure uvicorn logging
7. **Rate limit** - Add rate limiting middleware

## Security Considerations

**Important**: The HTTP server does NOT include authentication by default.

To secure:
1. Add API key middleware
2. Use HTTPS (TLS/SSL)
3. Restrict by IP/network
4. Use a reverse proxy with authentication
5. Enable CORS only for trusted origins

Example API key middleware:
```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != os.getenv("API_SECRET_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")
```

## Support

- Documentation: `docs/HTTP_SERVER_GUIDE.md`
- Issues: GitHub Issues
- Examples: `examples/http_client_examples/`

## Summary

The HTTP server provides:
- ✅ REST API for all MCP tools
- ✅ Prefix-based routing
- ✅ Streaming support (NDJSON)
- ✅ Automatic API docs
- ✅ Production-ready with FastAPI
- ✅ Complete separation from stdio MCP

Start using it today for web applications, mobile apps, or any HTTP client! 🚀
