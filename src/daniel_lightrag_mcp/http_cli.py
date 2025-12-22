"""
CLI entry point for the Daniel LightRAG MCP HTTP server.
"""

import argparse
import sys
from .http_server import run_server


def main():
    """Main CLI entry point for HTTP server."""
    parser = argparse.ArgumentParser(
        description="LightRAG MCP HTTP Server - Streamable HTTP API with prefix-based routing"
    )

    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)"
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )

    args = parser.parse_args()

    print(f"Starting LightRAG MCP HTTP Server on {args.host}:{args.port}")
    print(f"Prefix-based routing: /mcp/{{prefix}}/{{tool_name}}")
    print(f"Health check: http://{args.host}:{args.port}/health")
    print(f"\nPress Ctrl+C to stop the server")
    print("-" * 60)

    try:
        run_server(host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
