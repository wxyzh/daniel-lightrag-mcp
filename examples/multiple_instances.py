#!/usr/bin/env python3
"""
Example: Running Multiple LightRAG MCP Instances with Tool Prefixes

This example demonstrates how to configure and run multiple MCP server instances
with different prefixes to work with different LightRAG databases.
"""

import os
import subprocess
import sys
from pathlib import Path

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def main():
    print_section("LightRAG MCP Multiple Instance Configuration Example")

    print("This example shows how to configure multiple MCP instances with prefixes.")
    print()

    # Example 1: Novel Style Instance
    print_section("Instance 1: Novel Style Reference")
    print("Configuration for style reference queries:")
    print()
    print("  export LIGHTRAG_BASE_URL='http://localhost:9621'")
    print("  export LIGHTRAG_TOOL_PREFIX='novel_style_'")
    print("  python -m daniel_lightrag_mcp")
    print()
    print("Available tools will be:")
    print("  - novel_style_query_text")
    print("  - novel_style_insert_text")
    print("  - novel_style_get_documents")
    print("  - ... (all 22 tools with prefix)")
    print()
    print("Tool descriptions will show:")
    print("  [novel_style] Query LightRAG with text")
    print("  [novel_style] Insert text content into LightRAG")

    # Example 2: Novel Content Instance
    print_section("Instance 2: Novel Content")
    print("Configuration for content queries:")
    print()
    print("  export LIGHTRAG_BASE_URL='http://localhost:9622'")
    print("  export LIGHTRAG_TOOL_PREFIX='novel_content_'")
    print("  python -m daniel_lightrag_mcp")
    print()
    print("Available tools will be:")
    print("  - novel_content_query_text")
    print("  - novel_content_insert_text")
    print("  - novel_content_get_documents")
    print("  - ... (all 22 tools with prefix)")
    print()
    print("Tool descriptions will show:")
    print("  [novel_content] Query LightRAG with text")
    print("  [novel_content] Insert text content into LightRAG")

    # MCP Client Configuration
    print_section("MCP Client Configuration (e.g., Claude Desktop)")
    print("Add both instances to your MCP client configuration:")
    print()
    print('''{
  "mcpServers": {
    "lightrag-novel-style": {
      "command": "python",
      "args": ["-m", "daniel_lightrag_mcp"],
      "env": {
        "LIGHTRAG_BASE_URL": "http://localhost:9621",
        "LIGHTRAG_TOOL_PREFIX": "novel_style_"
      }
    },
    "lightrag-novel-content": {
      "command": "python",
      "args": ["-m", "daniel_lightrag_mcp"],
      "env": {
        "LIGHTRAG_BASE_URL": "http://localhost:9622",
        "LIGHTRAG_TOOL_PREFIX": "novel_content_"
      }
    }
  }
}''')

    # Usage Examples
    print_section("Usage Examples")
    print("Query style reference:")
    print('''{
  "tool": "novel_style_query_text",
  "arguments": {
    "query": "What writing style does this author use?",
    "mode": "hybrid"
  }
}''')
    print()
    print("Query novel content:")
    print('''{
  "tool": "novel_content_query_text",
  "arguments": {
    "query": "What happened in chapter 5?",
    "mode": "local"
  }
}''')

    # Benefits
    print_section("Benefits of Using Tool Prefixes")
    print("✓ Clear separation between different data sources")
    print("✓ No confusion about which database is being queried")
    print("✓ Easy to identify tools in MCP client")
    print("✓ Can run multiple instances in the same client")
    print("✓ Flexible prefix naming for different use cases")
    print()
    print("Common use cases:")
    print("  - research_      : Research database")
    print("  - docs_          : Documentation database")
    print("  - style_         : Style reference database")
    print("  - content_       : Content database")
    print("  - dev_           : Development/testing database")

    print_section("Quick Start")
    print("1. Start two LightRAG servers on different ports:")
    print("   lightrag --port 9621 --workdir ./novel_style")
    print("   lightrag --port 9622 --workdir ./novel_content")
    print()
    print("2. Configure MCP client with both instances (see above)")
    print()
    print("3. Restart MCP client to load the new configuration")
    print()
    print("4. Use prefixed tools to query different databases")

    print("\n")

if __name__ == "__main__":
    main()
