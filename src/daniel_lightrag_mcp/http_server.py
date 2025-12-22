"""
Streamable HTTP server for LightRAG MCP with prefix-based routing.

This module provides a FastAPI-based HTTP server that exposes MCP tools
via HTTP endpoints with prefix-based routing.

Routes:
    - POST /mcp/{prefix}/{tool_name} - Execute a tool
    - GET /mcp/{prefix}/tools - List tools for a prefix
    - GET /health - Health check
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from .client import LightRAGClient, LightRAGError
from .server import (
    _add_tool_prefix,
    _remove_tool_prefix,
    _validate_tool_arguments,
    handle_list_tools,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global client instances per prefix
clients: Dict[str, LightRAGClient] = {}


class ToolRequest(BaseModel):
    """Request model for tool execution."""
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    stream: bool = Field(default=False, description="Whether to stream the response")


class ToolResponse(BaseModel):
    """Response model for tool execution."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class ToolInfo(BaseModel):
    """Information about a tool."""
    name: str
    description: str
    input_schema: Dict[str, Any]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI app."""
    logger.info("Starting LightRAG HTTP Server")

    # Initialize clients for configured prefixes
    await initialize_clients()

    yield

    # Cleanup
    logger.info("Shutting down LightRAG HTTP Server")
    await cleanup_clients()


# Create FastAPI app
app = FastAPI(
    title="LightRAG MCP HTTP Server",
    description="Streamable HTTP API for LightRAG MCP tools with prefix-based routing",
    version="0.1.0",
    lifespan=lifespan,
)


async def initialize_clients():
    """Initialize LightRAG clients for all configured prefixes."""
    # Read timeout from environment
    timeout = float(os.getenv("LIGHTRAG_TIMEOUT", "300"))
    logger.info(f"Using timeout: {timeout} seconds")

    # Read prefix configurations from environment
    # Format: LIGHTRAG_HTTP_PREFIXES=prefix1:url1:key1,prefix2:url2:key2
    config = os.getenv("LIGHTRAG_HTTP_PREFIXES", "")

    if not config:
        logger.warning("No LIGHTRAG_HTTP_PREFIXES configured, using default")
        # Default configuration
        default_url = os.getenv("LIGHTRAG_BASE_URL", "http://localhost:9621")
        default_key = os.getenv("LIGHTRAG_API_KEY", "")
        clients["default"] = LightRAGClient(base_url=default_url, api_key=default_key, timeout=timeout)
        logger.info(f"Initialized default client: {default_url}")
        return

    # Parse configuration
    for item in config.split(","):
        item = item.strip()
        if not item:
            continue

        # Split on first colon only: prefix:url:key -> prefix, url:key
        first_colon = item.find(":")
        if first_colon > 0:
            prefix = item[:first_colon]
            rest = item[first_colon + 1:]

            # Handle URL with protocol (http://, https://)
            # Format: prefix:http://host:port or prefix:https://host:port:key
            if rest.startswith("http://"):
                url_part = rest[7:]  # Remove "http://"
                # Find the port in "host:port" or use empty key
                if ":" in url_part:
                    host, port = url_part.split(":", 1)
                    # Check if there's another colon for API key
                    if ":" in port:
                        port, api_key = port.split(":", 1)
                        url = f"http://{host}:{port}"
                    else:
                        url = f"http://{host}:{port}"
                        api_key = ""
                else:
                    url = f"http://{url_part}"
                    api_key = ""
            elif rest.startswith("https://"):
                url_part = rest[8:]  # Remove "https://"
                if ":" in url_part:
                    host, port = url_part.split(":", 1)
                    if ":" in port:
                        port, api_key = port.split(":", 1)
                        url = f"https://{host}:{port}"
                    else:
                        url = f"https://{host}:{port}"
                        api_key = ""
                else:
                    url = f"https://{url_part}"
                    api_key = ""
            else:
                # No protocol, simple format: url or url:key
                if ":" in rest:
                    url, api_key = rest.split(":", 1)
                else:
                    url = rest
                    api_key = ""

            clients[prefix] = LightRAGClient(base_url=url, api_key=api_key, timeout=timeout)
            logger.info(f"Initialized client for prefix '{prefix}': {url}")


async def cleanup_clients():
    """Cleanup all LightRAG clients."""
    for prefix, client in clients.items():
        try:
            await client.__aexit__(None, None, None)
            logger.info(f"Closed client for prefix '{prefix}'")
        except Exception as e:
            logger.error(f"Error closing client for '{prefix}': {e}")


def get_client(prefix: str) -> LightRAGClient:
    """Get LightRAG client for a prefix."""
    if prefix in clients:
        return clients[prefix]

    # Try default client
    if "default" in clients:
        logger.warning(f"No client for prefix '{prefix}', using default")
        return clients["default"]

    raise HTTPException(status_code=404, detail=f"No client configured for prefix: {prefix}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "prefixes": list(clients.keys()),
        "version": "0.1.0"
    }


@app.get("/mcp/{prefix}/tools")
async def list_tools(prefix: str):
    """List all tools for a specific prefix.

    Returns tools with URL path prefix prepended to their names.
    """
    try:
        # Validate prefix is configured
        if prefix not in clients:
            raise HTTPException(status_code=404, detail=f"Unknown prefix: {prefix}")

        # Get all tools
        tools = await handle_list_tools()

        # Return all tools with prefix prepended
        prefixed_tools = []
        for tool in tools:
            prefixed_tools.append(ToolInfo(
                name=f"{prefix}_{tool.name}",
                description=tool.description,
                input_schema=tool.inputSchema
            ))

        return {
            "prefix": prefix,
            "tools": [t.model_dump() for t in prefixed_tools],
            "count": len(prefixed_tools)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing tools for prefix '{prefix}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/{prefix}/{tool_name}")
async def execute_tool(prefix: str, tool_name: str, request: ToolRequest):
    """Execute a tool with the given arguments.

    URL path: /mcp/{prefix}/{prefix}_{actual_tool_name}
    """
    try:
        # Validate prefix is configured
        if prefix not in clients:
            raise HTTPException(status_code=404, detail=f"Unknown prefix: {prefix}")

        # Validate prefix matches tool_name
        expected_prefix = f"{prefix}_"
        if not tool_name.startswith(expected_prefix):
            raise HTTPException(
                status_code=400,
                detail=f"Tool name '{tool_name}' does not match prefix '{prefix}'"
            )

        # Get client for this prefix
        client = get_client(prefix)

        # Remove prefix to get actual tool name
        actual_tool_name = tool_name[len(expected_prefix):]

        # Validate arguments
        _validate_tool_arguments(actual_tool_name, request.arguments)

        logger.info(f"Executing tool: {tool_name} (actual: {actual_tool_name})")
        logger.debug(f"Arguments: {request.arguments}")

        # Check if streaming is requested
        if request.stream or "_stream" in actual_tool_name:
            return await execute_streaming_tool(client, actual_tool_name, request.arguments)
        else:
            return await execute_regular_tool(client, actual_tool_name, request.arguments)

    except LightRAGError as e:
        logger.error(f"LightRAG error: {e}")
        raise HTTPException(status_code=500, detail=e.to_dict())

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def execute_regular_tool(
    client: LightRAGClient,
    tool_name: str,
    arguments: Dict[str, Any]
) -> ToolResponse:
    """Execute a regular (non-streaming) tool using unified executor."""
    result = await client.execute_tool(tool_name, arguments)

    # Serialize result
    if hasattr(result, 'model_dump'):
        data = result.model_dump()
    elif hasattr(result, '__dict__'):
        data = result.__dict__
    else:
        data = result

    return ToolResponse(success=True, data=data)


async def execute_streaming_tool(
    client: LightRAGClient,
    tool_name: str,
    arguments: Dict[str, Any]
) -> StreamingResponse:
    """Execute a streaming tool and return streaming HTTP response."""
    # query_text_stream returns an async generator from the client
    stream_generator = client.query_text_stream(
        query=arguments["query"],
        mode=arguments.get("mode", "mix"),
        only_need_context=arguments.get("only_need_context", False),
        only_need_prompt=arguments.get("only_need_prompt", False),
        top_k=arguments.get("top_k"),
        max_entity_tokens=arguments.get("max_entity_tokens"),
        max_relation_tokens=arguments.get("max_relation_tokens"),
        include_references=arguments.get("include_references", True),
        include_chunk_content=arguments.get("include_chunk_content", False),
        enable_rerank=arguments.get("enable_rerank", True),
        conversation_history=arguments.get("conversation_history")
    )

    async def stream_wrapper() -> AsyncGenerator[bytes, None]:
        """Generate streaming response chunks."""
        try:
            async for chunk in stream_generator:
                # Send each chunk as NDJSON (newline-delimited JSON)
                yield (json.dumps({"type": "chunk", "data": chunk}) + "\n").encode("utf-8")

            # Send completion signal
            yield (json.dumps({"type": "done", "status": "completed"}) + "\n").encode("utf-8")

        except LightRAGError as e:
            error_data = {"type": "error", "error": str(e), "details": e.to_dict()}
            yield (json.dumps(error_data) + "\n").encode("utf-8")

        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            error_data = {"type": "error", "error": str(e)}
            yield (json.dumps(error_data) + "\n").encode("utf-8")

    return StreamingResponse(
        stream_wrapper(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        }
    )


@app.exception_handler(LightRAGError)
async def lightrag_error_handler(request: Request, exc: LightRAGError):
    """Handle LightRAG errors."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
            "details": exc.to_dict()
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail
        }
    )


def run_server(host: str = None, port: int = None):
    """Run the HTTP server."""
    import uvicorn

    # Read from environment variables if not provided
    if host is None:
        host = os.getenv("LIGHTRAG_HTTP_HOST", "127.0.0.1")
    if port is None:
        port = int(os.getenv("LIGHTRAG_HTTP_PORT", "8765"))

    logger.info(f"Starting HTTP server on {host}:{port}")
    logger.info(f"Environment: LIGHTRAG_HTTP_HOST={os.getenv('LIGHTRAG_HTTP_HOST', 'not set')}")
    logger.info(f"Environment: LIGHTRAG_HTTP_PORT={os.getenv('LIGHTRAG_HTTP_PORT', 'not set')}")

    uvicorn.run(
        "daniel_lightrag_mcp.http_server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
