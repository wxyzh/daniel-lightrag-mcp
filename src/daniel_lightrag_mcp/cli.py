"""
CLI entry point for the Daniel LightRAG MCP server.

Supports two modes:
- stdio (default): MCP server via stdio protocol
- http: REST API server via HTTP
"""

import argparse
import asyncio
import os
import sys


def cli():
    """CLI entry point with mode selection."""
    parser = argparse.ArgumentParser(
        description="Daniel LightRAG MCP Server - stdio or HTTP mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start stdio MCP server (default)
  daniel-lightrag-mcp

  # Start HTTP server
  daniel-lightrag-mcp --http

  # Start HTTP server with custom port
  daniel-lightrag-mcp --http --port 8080

  # Start HTTP server with custom host and port
  daniel-lightrag-mcp --http --host 127.0.0.1 --port 9000
        """
    )

    # Mode selection
    parser.add_argument(
        "--http",
        action="store_true",
        help="Start HTTP server instead of stdio MCP server"
    )

    # HTTP-specific options
    http_group = parser.add_argument_group("HTTP server options (only with --http)")

    default_host = os.getenv("LIGHTRAG_HTTP_HOST", "127.0.0.1")
    default_port = int(os.getenv("LIGHTRAG_HTTP_PORT", "8765"))

    http_group.add_argument(
        "--host",
        default=default_host,
        help=f"Host to bind the HTTP server to (default: {default_host}, env: LIGHTRAG_HTTP_HOST)"
    )

    http_group.add_argument(
        "--port",
        type=int,
        default=default_port,
        help=f"Port to bind the HTTP server to (default: {default_port}, env: LIGHTRAG_HTTP_PORT)"
    )

    http_group.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )

    args = parser.parse_args()

    # Dispatch to appropriate server
    if args.http:
        start_http_server(args)
    else:
        start_stdio_server()


def start_stdio_server():
    """Start the stdio MCP server."""
    from .server import main

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down stdio MCP server...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting stdio MCP server: {e}")
        sys.exit(1)


def start_http_server(args):
    """Start the HTTP server."""
    from .http_server import run_server

    print("=" * 70)
    print("LightRAG MCP HTTP Server")
    print("=" * 70)
    print(f"Starting HTTP server on {args.host}:{args.port}")
    print(f"Prefix-based routing: /mcp/{{prefix}}/{{tool_name}}")
    print(f"Health check: http://{args.host}:{args.port}/health")
    print(f"API docs: http://{args.host}:{args.port}/docs")
    print(f"\nPress Ctrl+C to stop the server")
    print("=" * 70)

    try:
        run_server(host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\n\nShutting down HTTP server...")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError starting HTTP server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
