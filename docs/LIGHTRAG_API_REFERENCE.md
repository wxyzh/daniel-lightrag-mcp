# LightRAG API Reference

**Version:** 1.0
**Last Updated:** 2025-12-22
**Base URL:** `http://localhost:9621` (configurable via `LIGHTRAG_BASE_URL`)

## Overview

The LightRAG API provides a complete REST interface for document management, knowledge graph operations, and querying. The MCP server wrapper provides 22 tools across 4 categories:

- **Document Management:** 7 tools for inserting, uploading, scanning, and managing documents
- **Query Operations:** 2 tools for text queries with 5 modes and 11 parameters
- **Knowledge Graph:** 9 tools for complete CRUD operations on entities and relations
- **System Management:** 4 tools for health checks, status monitoring, and cache management

## Authentication

### API Key Configuration

```bash
export LIGHTRAG_API_KEY="your-api-key"
python -m daniel_lightrag_mcp
```

```python
from daniel_lightrag_mcp.client import LightRAGClient

client = LightRAGClient(
    base_url="http://localhost:9621",
    api_key="your-api-key",
    timeout=30.0
)
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LIGHTRAG_BASE_URL` | `http://localhost:9621` | LightRAG server URL |
| `LIGHTRAG_API_KEY` | None | API key (optional) |
| `LIGHTRAG_TIMEOUT` | `30` | Request timeout in seconds |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LIGHTRAG_TOOL_PREFIX` | None | Tool name prefix for multiple instances |

## Document Management APIs

### 1. Insert Text
**Endpoint:** `POST /documents/text`

**Request:**
```json
{
  "text": "string (required)",
  "file_source": "string (default: 'text_input.txt')"
}
```

**Response:**
```json
{
  "status": "string",
  "message": "string",
  "track_id": "string | null",
  "id": "string | null"
}
```

**Python Example:**
```python
response = await client.insert_text(
    text="This is important information.",
    title="Document Title"
)
print(f"Inserted: {response.id}")
```

### 2. Insert Multiple Texts
**Endpoint:** `POST /documents/texts`

**Request:**
```json
{
  "texts": ["string", "string"],
  "file_sources": ["source1.txt", "source2.txt"]
}
```

**Python Example:**
```python
from daniel_lightrag_mcp.models import TextDocument

texts = [
    TextDocument(title="AI Overview", content="AI is..."),
    TextDocument(content="ML algorithms...")
]
response = await client.insert_texts(texts)
```

### 3. Upload Document
**Endpoint:** `POST /documents/upload`

**Request:** Multipart form data with file

**Python Example:**
```python
response = await client.upload_document("/path/to/file.pdf")
print(f"Track ID: {response.track_id}")
```

### 4. Get Documents (Paginated)
**Endpoint:** `POST /documents/paginated`

**Request:**
```json
{
  "page": 1,
  "page_size": 20,
  "status_filter": "processed"
}
```

**Response:**
```json
{
  "documents": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_count": 100,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  },
  "status_counts": {...}
}
```

### 5. Delete Document
**Endpoint:** `DELETE /documents/delete_document`

**Request:**
```json
{
  "doc_ids": ["doc_123", "doc_456"],
  "delete_file": false,
  "delete_llm_cache": false
}
```

**Python Example:**
```python
response = await client.delete_document(
    ["doc_123", "doc_456"],
    delete_file=True,
    delete_llm_cache=True
)
```

## Query APIs

### Query Modes

| Mode | Description | Best For |
|------|-------------|----------|
| `naive` | Simple vector search | Quick keyword searches |
| `local` | Entity-focused retrieval | Detailed entity questions |
| `global` | Community summaries | Comprehensive overviews |
| `hybrid` | Combines local+global | Balanced queries (default) |
| `mix` | Knowledge graph + vector | Complex multi-aspect queries |

### Query Text
**Endpoint:** `POST /query`

**Request:**
```json
{
  "query": "string (required)",
  "mode": "hybrid",
  "only_need_context": false,
  "only_need_prompt": false,
  "top_k": null,
  "max_entity_tokens": null,
  "max_relation_tokens": null,
  "include_references": false,
  "include_chunk_content": false,
  "enable_rerank": false,
  "conversation_history": null
}
```

**Response:**
```json
{
  "response": "string | null",
  "query": "string | null",
  "results": [...],
  "total_results": 10,
  "processing_time": 1.234,
  "context": "string | null"
}
```

**Python Example:**
```python
response = await client.query_text(
    query="What are transformers in ML?",
    mode="hybrid",
    top_k=10,
    include_references=True,
    enable_rerank=True
)
print(f"Response: {response.response}")
print(f"Found {response.total_results} results")
```

### Advanced Query Parameters

- **top_k**: Number of top results to retrieve
- **max_entity_tokens**: Token limit for entity context (local mode)
- **max_relation_tokens**: Token limit for relation context (global mode)
- **include_references**: Include source references in response
- **include_chunk_content**: Include full chunk content (requires include_references)
- **enable_rerank**: Enable result reranking for better quality
- **conversation_history**: Multi-turn conversation context
  ```json
  [
    {"role": "user", "content": "What is AI?"},
    {"role": "assistant", "content": "AI is..."}
  ]
  ```

### Query Text Stream
**Endpoint:** `POST /query/stream`

Same parameters as Query Text, returns Server-Sent Events (SSE) stream.

**Python Example:**
```python
async for chunk in client.query_text_stream(
    query="Explain AI evolution",
    mode="global"
):
    print(chunk, end='', flush=True)
```

## Knowledge Graph APIs

### 1. Get Knowledge Graph
**Endpoint:** `GET /graphs?label=*`

**Response:**
```json
{
  "nodes": [{"id": "...", "name": "...", "type": "...", "properties": {}}],
  "edges": [{"id": "...", "source": "...", "target": "...", "weight": 0.9}],
  "is_truncated": false
}
```

### 2. Create Entity
**Endpoint:** `POST /graph/entity/create`

**Request:**
```json
{
  "entity_name": "Neural Networks",
  "properties": {
    "description": "Computational models...",
    "entity_type": "Technology"
  }
}
```

**Python Example:**
```python
response = await client.create_entity(
    entity_name="Neural Networks",
    properties={
        "description": "Computational models",
        "entity_type": "Technology"
    }
)
```

### 3. Create Relation
**Endpoint:** `POST /graph/relation/create`

**Request:**
```json
{
  "source_entity": "Machine Learning",
  "target_entity": "Neural Networks",
  "properties": {
    "description": "NN is subset of ML",
    "weight": 0.9
  }
}
```

### 4. Update Entity
**Endpoint:** `POST /graph/entity/edit`

**Request:**
```json
{
  "entity_id": "entity_123",
  "entity_name": "Neural Networks",
  "updated_data": {"description": "Updated description"}
}
```

### 5. Update Relation
**Endpoint:** `POST /graph/relation/edit`

**Request:**
```json
{
  "source_id": "entity_123",
  "target_id": "entity_456",
  "updated_data": {"weight": 0.95}
}
```

### 6. Delete Entity
**Endpoint:** `DELETE /rag/delete_by_entity`

**Request:**
```json
{
  "entity_id": "entity_123",
  "entity_name": "Machine Learning"
}
```

### 7. Delete Relation
**Endpoint:** `DELETE /rag/delete_by_relation`

**Request:**
```json
{
  "relation_id": "rel_123",
  "source_entity": "ML",
  "target_entity": "NN"
}
```

## System Management APIs

### 1. Get Pipeline Status
**Endpoint:** `GET /documents/pipeline_status`

**Response:**
```json
{
  "autoscanned": true,
  "busy": false,
  "job_name": "string | null",
  "docs": 150,
  "batchs": 3,
  "cur_batch": 2,
  "progress": 66.7,
  "current_task": "string | null"
}
```

### 2. Get Track Status
**Endpoint:** `GET /documents/track_status/{track_id}`

**Response:**
```json
{
  "track_id": "string",
  "documents": [...],
  "total_count": 5,
  "status_summary": {
    "pending": 0,
    "processing": 1,
    "processed": 4,
    "failed": 0
  }
}
```

### 3. Get Document Status Counts
**Endpoint:** `GET /documents/status_counts`

**Response:**
```json
{
  "status_counts": {
    "pending": 5,
    "processing": 2,
    "processed": 145,
    "failed": 3
  }
}
```

### 4. Health Check
**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "ok | degraded | error",
  "version": "string | null",
  "uptime": 3600.5,
  "database_status": "string | null",
  "cache_status": "string | null"
}
```

## Error Handling

### Exception Hierarchy

```
LightRAGError
├── LightRAGConnectionError
├── LightRAGAuthError
├── LightRAGValidationError
├── LightRAGAPIError
├── LightRAGTimeoutError
└── LightRAGServerError
```

### Error Response Format

```json
{
  "error_type": "LightRAGConnectionError",
  "message": "Connection failed",
  "status_code": null,
  "response_data": {}
}
```

### Exception Handling Example

```python
from daniel_lightrag_mcp.client import (
    LightRAGClient,
    LightRAGError,
    LightRAGValidationError
)

try:
    response = await client.query_text("")
except LightRAGValidationError as e:
    print(f"Validation error: {e.message}")
except LightRAGError as e:
    error_dict = e.to_dict()
    print(f"Error: {error_dict}")
```

## Complete Workflow Examples

### Example 1: Document Upload and Query

```python
from daniel_lightrag_mcp.client import LightRAGClient
import asyncio

async def workflow():
    client = LightRAGClient(base_url="http://localhost:9621")

    # Check health
    health = await client.get_health()
    print(f"Server status: {health.status}")

    # Upload document
    upload = await client.upload_document("/path/to/doc.pdf")
    print(f"Track ID: {upload.track_id}")

    # Query
    result = await client.query_text(
        query="What is the main topic?",
        mode="hybrid",
        include_references=True
    )
    print(f"Response: {result.response}")

    await client.client.aclose()

asyncio.run(workflow())
```

### Example 2: Knowledge Graph Management

```python
async def kg_workflow():
    client = LightRAGClient()

    # Create entities
    ml = await client.create_entity(
        entity_name="Machine Learning",
        properties={"entity_type": "Technology"}
    )

    nn = await client.create_entity(
        entity_name="Neural Networks",
        properties={"entity_type": "Technology"}
    )

    # Create relation
    rel = await client.create_relation(
        source_entity="Machine Learning",
        target_entity="Neural Networks",
        properties={"weight": 0.95}
    )

    # Get graph
    graph = await client.get_knowledge_graph()
    print(f"Entities: {len(graph.nodes)}")
    print(f"Relations: {len(graph.edges)}")

    await client.client.aclose()

asyncio.run(kg_workflow())
```

## Best Practices

1. **Health Checks**: Always start with `get_health()` to verify connectivity
2. **Error Handling**: Wrap all API calls in try-except blocks
3. **Pagination**: Use paginated retrieval for large document sets
4. **Query Optimization**:
   - Use `naive` for simple keyword searches
   - Use `hybrid` or `mix` for comprehensive queries
   - Enable `enable_rerank=True` for better quality results
5. **Batch Operations**: Use `insert_texts()` instead of multiple `insert_text()` calls
6. **Monitoring**: Check pipeline status for long-running operations
7. **Cache Management**: Clear cache periodically for optimal performance

## Additional Resources

- **LightRAG Repository**: https://github.com/GAIR-NLP/LightRAG
- **MCP Protocol**: https://modelcontextprotocol.io/
- **Project Repository**: https://github.com/yourusername/daniel-lightrag-mcp

---

*Document generated from codebase analysis on 2025-12-22*
