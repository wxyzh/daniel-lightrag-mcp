# Tool Prefix Feature - Quick Reference

## Overview

The tool prefix feature allows you to run multiple LightRAG MCP server instances simultaneously, each with a unique prefix for its tools. This is essential when you need to work with multiple separate LightRAG databases.

## Key Use Cases

1. **Novel Writing**: Separate databases for style references and content
2. **Multi-Project**: Different databases for different projects
3. **Multi-Language**: Separate databases for different languages
4. **Environment Separation**: Dev, staging, and production databases

## How It Works

### Environment Variable

Set `LIGHTRAG_TOOL_PREFIX` to add a prefix to all tool names and descriptions:

```bash
export LIGHTRAG_TOOL_PREFIX="novel_style_"
```

### Effect on Tools

**Without Prefix:**
- Tool name: `query_text`
- Description: `Query LightRAG with text`

**With Prefix `novel_style_`:**
- Tool name: `novel_style_query_text`
- Description: `[novel_style] Query LightRAG with text`

## Quick Setup (2 Instances)

### 1. Start Two LightRAG Servers

```bash
# Terminal 1: Style database
lightrag --port 9621 --workdir ./databases/style

# Terminal 2: Content database
lightrag --port 9622 --workdir ./databases/content
```

### 2. Configure Claude Desktop

Edit `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "lightrag-style": {
      "command": "python",
      "args": ["-m", "daniel_lightrag_mcp"],
      "env": {
        "LIGHTRAG_BASE_URL": "http://localhost:9621",
        "LIGHTRAG_TOOL_PREFIX": "style_"
      }
    },
    "lightrag-content": {
      "command": "python",
      "args": ["-m", "daniel_lightrag_mcp"],
      "env": {
        "LIGHTRAG_BASE_URL": "http://localhost:9622",
        "LIGHTRAG_TOOL_PREFIX": "content_"
      }
    }
  }
}
```

### 3. Restart Claude Desktop

### 4. Use Prefixed Tools

```json
// Query style database
{
  "tool": "style_query_text",
  "arguments": {"query": "What writing style is used?"}
}

// Query content database
{
  "tool": "content_query_text",
  "arguments": {"query": "Summarize chapter 5"}
}
```

## All Available Prefixed Tools

When you set a prefix (e.g., `novel_`), all 20+ tools get the prefix:

### Document Management
- `novel_insert_text`
- `novel_insert_texts`
- `novel_upload_document`
- `novel_scan_documents`
- `novel_get_documents`
- `novel_get_documents_paginated`
- `novel_delete_document`

### Query Operations
- `novel_query_text`
- `novel_query_text_stream`

### Knowledge Graph
- `novel_get_knowledge_graph`
- `novel_get_graph_labels`
- `novel_check_entity_exists`
- `novel_update_entity`
- `novel_update_relation`
- `novel_delete_entity`
- `novel_delete_relation`

### System Management
- `novel_get_pipeline_status`
- `novel_get_track_status`
- `novel_get_document_status_counts`
- `novel_get_health`

## Testing Your Setup

### Test Prefix Functions

```bash
cd examples
python test_prefix_demo.py
```

Expected output:
```
Tool prefix enabled: 'novel_style_'
add_tool_prefix(query_text) -> novel_style_query_text
remove_tool_prefix(novel_style_query_text) -> query_text
add_description_prefix(Test) -> [novel_style] Test
```

### Test MCP Configuration

Use the quick start script:

```bash
cd examples
python quick_start_multiple.py
```

This will generate a complete configuration and guide you through setup.

## Common Prefix Patterns

| Use Case | Prefix | Example Tool |
|----------|--------|--------------|
| Novel style | `style_` | `style_query_text` |
| Novel content | `content_` | `content_query_text` |
| Research | `research_` | `research_query_text` |
| Documentation | `docs_` | `docs_query_text` |
| Development | `dev_` | `dev_query_text` |
| Chinese content | `zh_` | `zh_query_text` |
| English content | `en_` | `en_query_text` |
| Project Alpha | `alpha_` | `alpha_query_text` |
| Project Beta | `beta_` | `beta_query_text` |

## Troubleshooting

### Problem: Tools don't have prefix

**Solution:** Check environment variable is set in MCP config

```json
{
  "env": {
    "LIGHTRAG_TOOL_PREFIX": "your_prefix_"
  }
}
```

### Problem: Can't connect to server

**Solution:** Verify LightRAG server is running on correct port

```bash
curl http://localhost:9621/health
```

### Problem: Tools from different instances have same names

**Solution:** Ensure each instance has a unique prefix

## Best Practices

1. **Use descriptive prefixes**: `novel_style_` not just `ns_`
2. **Keep prefixes consistent**: Don't mix `style_` and `styles_`
3. **End with underscore**: `prefix_` not `prefix`
4. **Document your setup**: Keep notes on which prefix maps to which database
5. **Test independently**: Verify each instance works before combining

## More Information

- **Complete Guide**: `docs/MULTIPLE_INSTANCES_GUIDE.md`
- **Examples**: `examples/multiple_instances.py`
- **Tests**: `tests/test_tool_prefix.py`
- **Main README**: `README.md`

## Summary

The tool prefix feature enables powerful multi-database workflows by:
- ✓ Preventing tool name collisions
- ✓ Clearly identifying which database each tool operates on
- ✓ Supporting unlimited simultaneous instances
- ✓ Maintaining clean separation of concerns
- ✓ Simplifying complex multi-source projects

Start using it today to supercharge your LightRAG MCP setup!
