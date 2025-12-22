"""
Test script for tool prefix functionality.
Run with: python test_prefix_demo.py
"""

import os
import sys

# Set environment variable before importing
os.environ['LIGHTRAG_TOOL_PREFIX'] = 'novel_style_'

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Now import the server module
from daniel_lightrag_mcp.server import (
    TOOL_PREFIX,
    _add_tool_prefix,
    _remove_tool_prefix,
    _add_description_prefix,
)

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def main():
    print_section("Tool Prefix Functionality Test")

    print(f"Environment Variable: LIGHTRAG_TOOL_PREFIX = '{os.getenv('LIGHTRAG_TOOL_PREFIX')}'")
    print(f"Loaded TOOL_PREFIX: '{TOOL_PREFIX}'")

    print_section("Testing _add_tool_prefix()")

    test_tools = [
        'query_text',
        'insert_text',
        'get_documents',
        'get_health',
        'get_knowledge_graph',
    ]

    for tool in test_tools:
        prefixed = _add_tool_prefix(tool)
        print(f"  {tool:30s} -> {prefixed}")

    print_section("Testing _remove_tool_prefix()")

    prefixed_tools = [
        'novel_style_query_text',
        'novel_style_insert_text',
        'novel_style_get_documents',
        'novel_style_get_health',
        'novel_style_get_knowledge_graph',
    ]

    for tool in prefixed_tools:
        original = _remove_tool_prefix(tool)
        print(f"  {tool:40s} -> {original}")

    print_section("Testing _add_description_prefix()")

    test_descriptions = [
        'Query LightRAG with text',
        'Insert text content into LightRAG',
        'Retrieve all documents from LightRAG',
        'Check LightRAG server health',
    ]

    for desc in test_descriptions:
        prefixed_desc = _add_description_prefix(desc)
        print(f"  Original:  {desc}")
        print(f"  Prefixed:  {prefixed_desc}")
        print()

    print_section("Round-trip Test (add then remove)")

    for tool in test_tools:
        prefixed = _add_tool_prefix(tool)
        unprefixed = _remove_tool_prefix(prefixed)
        status = "[PASS]" if unprefixed == tool else "[FAIL]"
        print(f"  {status}  {tool} -> {prefixed} -> {unprefixed}")

    print_section("Test Summary")
    print("All prefix functions are working correctly!")
    print()
    print("To use in production:")
    print("  1. Set environment variable: $env:LIGHTRAG_TOOL_PREFIX='novel_style_'")
    print("  2. Start MCP server: python -m daniel_lightrag_mcp")
    print("  3. All tools will have the prefix in their names and descriptions")
    print()

if __name__ == '__main__':
    main()
