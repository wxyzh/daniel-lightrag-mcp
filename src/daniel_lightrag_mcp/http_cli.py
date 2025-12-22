"""
Shortcut CLI entry point for the Daniel LightRAG HTTP server.

This is a convenience wrapper that automatically starts the HTTP server.
Equivalent to: daniel-lightrag-mcp --http
"""

import sys


def main():
    """Main CLI entry point for HTTP server (shortcut)."""
    # Add --http flag to argv if not already present
    if "--http" not in sys.argv:
        sys.argv.insert(1, "--http")

    # Import and run the main CLI
    from .cli import cli
    cli()


if __name__ == "__main__":
    main()
