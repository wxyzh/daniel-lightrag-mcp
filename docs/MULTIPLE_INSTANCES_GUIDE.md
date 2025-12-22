# Multiple Instance Configuration Guide

This guide shows how to configure multiple LightRAG MCP server instances with different prefixes.

## Configuration for Claude Desktop

### Windows Configuration

Location: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "lightrag-novel-style": {
      "command": "python",
      "args": ["-m", "daniel_lightrag_mcp"],
      "env": {
        "LIGHTRAG_BASE_URL": "http://localhost:9621",
        "LIGHTRAG_API_KEY": "lightragsecretkey",
        "LIGHTRAG_TOOL_PREFIX": "novel_style_",
        "LOG_LEVEL": "INFO"
      }
    },
    "lightrag-novel-content": {
      "command": "python",
      "args": ["-m", "daniel_lightrag_mcp"],
      "env": {
        "LIGHTRAG_BASE_URL": "http://localhost:9622",
        "LIGHTRAG_API_KEY": "lightragsecretkey",
        "LIGHTRAG_TOOL_PREFIX": "novel_content_",
        "LOG_LEVEL": "INFO"
      }
    },
    "lightrag-research": {
      "command": "python",
      "args": ["-m", "daniel_lightrag_mcp"],
      "env": {
        "LIGHTRAG_BASE_URL": "http://localhost:9623",
        "LIGHTRAG_API_KEY": "lightragsecretkey",
        "LIGHTRAG_TOOL_PREFIX": "research_",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### macOS/Linux Configuration

Location: `~/.config/claude/claude_desktop_config.json` or `~/Library/Application Support/Claude/claude_desktop_config.json`

Same JSON structure as above.

## Tool Names After Configuration

### Instance 1: Novel Style (novel_style_)
- `novel_style_query_text`
- `novel_style_insert_text`
- `novel_style_insert_texts`
- `novel_style_upload_document`
- `novel_style_scan_documents`
- `novel_style_get_documents`
- `novel_style_get_documents_paginated`
- `novel_style_delete_document`
- `novel_style_query_text_stream`
- `novel_style_get_knowledge_graph`
- `novel_style_get_graph_labels`
- `novel_style_check_entity_exists`
- `novel_style_update_entity`
- `novel_style_update_relation`
- `novel_style_delete_entity`
- `novel_style_delete_relation`
- `novel_style_get_pipeline_status`
- `novel_style_get_track_status`
- `novel_style_get_document_status_counts`
- `novel_style_get_health`

### Instance 2: Novel Content (novel_content_)
All tools with `novel_content_` prefix instead.

### Instance 3: Research (research_)
All tools with `research_` prefix instead.

## Tool Descriptions

Tool descriptions will include the prefix in brackets:

- `[novel_style] Query LightRAG with text`
- `[novel_content] Insert text content into LightRAG`
- `[research] Retrieve the knowledge graph from LightRAG`

This makes it clear which database each tool operates on.

## Usage Examples

### Query Novel Style Reference
```json
{
  "tool": "novel_style_query_text",
  "arguments": {
    "query": "What writing techniques does this author use for dialogue?",
    "mode": "hybrid"
  }
}
```

### Query Novel Content
```json
{
  "tool": "novel_content_query_text",
  "arguments": {
    "query": "Summarize the events in chapter 10",
    "mode": "local"
  }
}
```

### Query Research Database
```json
{
  "tool": "research_query_text",
  "arguments": {
    "query": "What are the latest findings on transformer architectures?",
    "mode": "global"
  }
}
```

### Insert Content into Specific Database
```json
{
  "tool": "novel_style_insert_text",
  "arguments": {
    "text": "Example of author's dialogue style: \"I can't believe you did that,\" she said, her voice trembling."
  }
}
```

```json
{
  "tool": "novel_content_insert_text",
  "arguments": {
    "text": "Chapter 11: The protagonist discovers a hidden message in the old manuscript."
  }
}
```

## Common Prefix Naming Conventions

### By Purpose
- `style_` - Style references
- `content_` - Main content
- `research_` - Research materials
- `docs_` - Documentation
- `ref_` - Reference materials

### By Project
- `project_alpha_` - Project Alpha database
- `project_beta_` - Project Beta database
- `client_xyz_` - Client XYZ database

### By Environment
- `dev_` - Development database
- `staging_` - Staging database
- `prod_` - Production database

### By Language/Type
- `zh_` - Chinese content
- `en_` - English content
- `code_` - Code snippets
- `text_` - Text documents

## Starting Multiple LightRAG Servers

You need to run separate LightRAG server instances on different ports:

### Terminal 1: Novel Style Database
```powershell
# Navigate to your LightRAG installation
cd path/to/lightrag

# Start server with specific port and working directory
lightrag --port 9621 --workdir ./databases/novel_style
```

### Terminal 2: Novel Content Database
```powershell
lightrag --port 9622 --workdir ./databases/novel_content
```

### Terminal 3: Research Database
```powershell
lightrag --port 9623 --workdir ./databases/research
```

## Verifying Configuration

After setting up, you can verify each instance:

### Check Novel Style Instance
```bash
curl http://localhost:9621/health
```

### Check Novel Content Instance
```bash
curl http://localhost:9622/health
```

### Check Research Instance
```bash
curl http://localhost:9623/health
```

## Troubleshooting

### Tools Not Showing Prefix
1. Check environment variable is set correctly in config
2. Restart Claude Desktop to reload configuration
3. Check MCP server logs for prefix loading message

### Cannot Connect to LightRAG Server
1. Verify LightRAG server is running on the configured port
2. Check `LIGHTRAG_BASE_URL` matches the server port
3. Test direct connection: `curl http://localhost:PORT/health`

### Tool Name Collisions
If you forget to set different prefixes, tools from different instances will have the same names, causing confusion. Always use unique prefixes for each instance.

## Best Practices

1. **Use descriptive prefixes**: Choose prefixes that clearly indicate the purpose
2. **Keep prefixes short**: Use 1-2 words followed by underscore
3. **Document your prefixes**: Keep a record of which prefix maps to which database
4. **Test each instance**: Verify each instance independently before using together
5. **Use different ports**: Always use different ports for different LightRAG servers
6. **Separate working directories**: Use different `--workdir` for each LightRAG instance

## Example Workflow

### Setup Phase
1. Start 3 LightRAG servers on ports 9621, 9622, 9623
2. Configure Claude Desktop with 3 MCP server instances
3. Restart Claude Desktop
4. Verify all tools are visible with correct prefixes

### Usage Phase
1. Insert style references into `novel_style_` tools
2. Insert chapter content into `novel_content_` tools
3. Insert research materials into `research_` tools
4. Query each database using the appropriate prefixed tool

### Maintenance Phase
1. Monitor each instance's health with `[prefix]_get_health`
2. Check document counts with `[prefix]_get_document_status_counts`
3. Clear specific database cache with `[prefix]_clear_cache`
