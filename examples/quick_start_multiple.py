#!/usr/bin/env python3
"""
Quick Start Script for Multiple MCP Instances

This script helps you quickly set up and test multiple LightRAG MCP instances
with different prefixes.

Usage:
    python quick_start_multiple.py
"""

import json
import os
import sys
from pathlib import Path


def print_header(text):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_step(number, text):
    """Print a numbered step."""
    print(f"\n[Step {number}] {text}")
    print("-" * 70)


def generate_config():
    """Generate MCP client configuration."""
    config = {
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
            }
        }
    }
    return config


def main():
    print_header("LightRAG MCP Multiple Instances - Quick Start")

    print("This script will guide you through setting up multiple MCP instances")
    print("with different tool prefixes for different LightRAG databases.")
    print()

    # Step 1: Prerequisites
    print_step(1, "Prerequisites Check")
    print("Before proceeding, ensure you have:")
    print("  [1] Python 3.8+ installed")
    print("  [2] daniel-lightrag-mcp package installed (pip install -e .)")
    print("  [3] LightRAG server available")
    print()
    response = input("Do you have all prerequisites ready? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("\nPlease install prerequisites first. See README.md for details.")
        return

    # Step 2: Generate Configuration
    print_step(2, "Generate MCP Configuration")
    config = generate_config()
    config_json = json.dumps(config, indent=2)

    print("\nGenerated configuration:")
    print(config_json)
    print()

    # Save configuration
    config_file = Path("mcp_config_example.json")
    config_file.write_text(config_json, encoding='utf-8')
    print(f"Configuration saved to: {config_file.absolute()}")

    # Step 3: Configuration Location
    print_step(3, "Claude Desktop Configuration")

    if sys.platform == 'win32':
        config_path = Path(os.environ.get('APPDATA', '')) / 'Claude' / 'claude_desktop_config.json'
    elif sys.platform == 'darwin':
        config_path = Path.home() / 'Library' / 'Application Support' / 'Claude' / 'claude_desktop_config.json'
    else:
        config_path = Path.home() / '.config' / 'claude' / 'claude_desktop_config.json'

    print(f"Your Claude Desktop config should be at:")
    print(f"  {config_path}")
    print()
    print("Please:")
    print("  1. Copy the configuration above")
    print("  2. Add it to your claude_desktop_config.json file")
    print("  3. Adjust ports and prefixes as needed")

    # Step 4: Start LightRAG Servers
    print_step(4, "Start LightRAG Servers")
    print("You need to start LightRAG servers on different ports:")
    print()
    print("Terminal 1 (Novel Style):")
    print("  lightrag --port 9621 --workdir ./databases/novel_style")
    print()
    print("Terminal 2 (Novel Content):")
    print("  lightrag --port 9622 --workdir ./databases/novel_content")
    print()

    # Step 5: Testing
    print_step(5, "Testing the Setup")
    print("After starting LightRAG servers and configuring Claude Desktop:")
    print()
    print("1. Restart Claude Desktop")
    print("2. Open a new conversation")
    print("3. Check available MCP tools - you should see:")
    print("   - novel_style_query_text")
    print("   - novel_style_insert_text")
    print("   - novel_content_query_text")
    print("   - novel_content_insert_text")
    print("   - ... (all tools with prefixes)")
    print()
    print("4. Test each instance:")
    print("   Use: novel_style_get_health")
    print("   Use: novel_content_get_health")

    # Step 6: Example Usage
    print_step(6, "Example Usage")
    print("Insert style reference:")
    print(json.dumps({
        "tool": "novel_style_insert_text",
        "arguments": {
            "text": "Author's dialogue style example..."
        }
    }, indent=2))
    print()
    print("Insert chapter content:")
    print(json.dumps({
        "tool": "novel_content_insert_text",
        "arguments": {
            "text": "Chapter 1 content..."
        }
    }, indent=2))
    print()
    print("Query style database:")
    print(json.dumps({
        "tool": "novel_style_query_text",
        "arguments": {
            "query": "What dialogue techniques are used?",
            "mode": "hybrid"
        }
    }, indent=2))

    # Summary
    print_header("Setup Complete!")
    print("Next steps:")
    print("  1. Start your LightRAG servers")
    print("  2. Update Claude Desktop configuration")
    print("  3. Restart Claude Desktop")
    print("  4. Start using prefixed tools!")
    print()
    print("For more details, see:")
    print("  - docs/MULTIPLE_INSTANCES_GUIDE.md")
    print("  - examples/multiple_instances.py")
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)
