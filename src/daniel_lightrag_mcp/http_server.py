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
    # Read prefix configurations from environment
    # Format: LIGHTRAG_HTTP_PREFIXES=prefix1:url1:key1,prefix2:url2:key2
    config = os.getenv("LIGHTRAG_HTTP_PREFIXES", "")

    if not config:
        logger.warning("No LIGHTRAG_HTTP_PREFIXES configured, using default")
        # Default configuration
        default_url = os.getenv("LIGHTRAG_BASE_URL", "http://localhost:9621")
        default_key = os.getenv("LIGHTRAG_API_KEY", "")
        clients["default"] = LightRAGClient(base_url=default_url, api_key=default_key)
        logger.info(f"Initialized default client: {default_url}")
        return

    # Parse configuration
    for item in config.split(","):
        parts = item.strip().split(":")
        if len(parts) >= 2:
            prefix = parts[0]
            url = parts[1]
            api_key = parts[2] if len(parts) > 2 else ""

            clients[prefix] = LightRAGClient(base_url=url, api_key=api_key)
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
    """List all tools for a specific prefix."""
    try:
        # Get all tools
        tools = await handle_list_tools()

        # Filter tools by prefix
        prefixed_tools = []
        for tool in tools:
            if tool.name.startswith(f"{prefix}_"):
                prefixed_tools.append(ToolInfo(
                    name=tool.name,
                    description=tool.description,
                    input_schema=tool.inputSchema
                ))

        return {
            "prefix": prefix,
            "tools": [t.model_dump() for t in prefixed_tools],
            "count": len(prefixed_tools)
        }

    except Exception as e:
        logger.error(f"Error listing tools for prefix '{prefix}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/{prefix}/{tool_name}")
async def execute_tool(prefix: str, tool_name: str, request: ToolRequest):
    """Execute a tool with the given arguments."""
    try:
        # Validate prefix matches tool_name
        if not tool_name.startswith(f"{prefix}_"):
            raise HTTPException(
                status_code=400,
                detail=f"Tool name '{tool_name}' does not match prefix '{prefix}'"
            )

        # Get client for this prefix
        client = get_client(prefix)

        # Remove prefix to get actual tool name
        actual_tool_name = _remove_tool_prefix(tool_name)

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
    """Execute a regular (non-streaming) tool."""

    # Document Management Tools
    if tool_name == "insert_text":
        result = await client.insert_text(arguments["text"])

    elif tool_name == "insert_texts":
        result = await client.insert_texts(arguments["texts"])

    elif tool_name == "upload_document":
        result = await client.upload_document(arguments["file_path"])

    elif tool_name == "scan_documents":
        result = await client.scan_documents()

    elif tool_name == "get_documents":
        result = await client.get_documents()

    elif tool_name == "get_documents_paginated":
        result = await client.get_documents_paginated(
            arguments["page"],
            arguments["page_size"]
        )

    elif tool_name == "delete_document":
        doc_ids = arguments.get("document_ids") or [arguments.get("document_id")]
        result = await client.delete_document(
            doc_ids=doc_ids,
            delete_file=arguments.get("delete_file", False),
            delete_llm_cache=arguments.get("delete_llm_cache", False)
        )

    # Query Tools
    elif tool_name == "query_text":
        result = await client.query_text(
            arguments["query"],
            mode=arguments.get("mode", "hybrid"),
            only_need_context=arguments.get("only_need_context", False)
        )

    # Knowledge Graph Tools
    elif tool_name == "get_knowledge_graph":
        result = await client.get_knowledge_graph()

    elif tool_name == "get_graph_labels":
        result = await client.get_graph_labels()

    elif tool_name == "check_entity_exists":
        result = await client.check_entity_exists(arguments["entity_name"])

    elif tool_name == "update_entity":
        result = await client.update_entity(
            arguments["entity_id"],
            arguments["properties"]
        )

    elif tool_name == "update_relation":
        result = await client.update_relation(
            arguments["source_id"],
            arguments["target_id"],
            arguments["updated_data"]
        )

    elif tool_name == "delete_entity":
        result = await client.delete_entity(arguments["entity_id"])

    elif tool_name == "delete_relation":
        result = await client.delete_relation(arguments["relation_id"])

    # System Management Tools
    elif tool_name == "get_pipeline_status":
        result = await client.get_pipeline_status()

    elif tool_name == "get_track_status":
        result = await client.get_track_status(arguments["track_id"])

    elif tool_name == "get_document_status_counts":
        result = await client.get_document_status_counts()

    elif tool_name == "get_health":
        result = await client.get_health()

    else:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")

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

    async def stream_generator() -> AsyncGenerator[bytes, None]:
        """Generate streaming response chunks."""
        try:
            if tool_name == "query_text_stream":
                async for chunk in client.query_text_stream(
                    arguments["query"],
                    mode=arguments.get("mode", "hybrid"),
                    only_need_context=arguments.get("only_need_context", False)
                ):
                    # Send each chunk as NDJSON (newline-delimited JSON)
                    yield (json.dumps({"type": "chunk", "data": chunk}) + "\n").encode("utf-8")

                # Send completion signal
                yield (json.dumps({"type": "done", "status": "completed"}) + "\n").encode("utf-8")

            else:
                raise HTTPException(status_code=400, detail=f"Tool '{tool_name}' does not support streaming")

        except LightRAGError as e:
            error_data = {"type": "error", "error": str(e), "details": e.to_dict()}
            yield (json.dumps(error_data) + "\n").encode("utf-8")

        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            error_data = {"type": "error", "error": str(e)}
            yield (json.dumps(error_data) + "\n").encode("utf-8")

    return StreamingResponse(
        stream_generator(),
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


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the HTTP server."""
    import uvicorn

    logger.info(f"Starting HTTP server on {host}:{port}")
    uvicorn.run(
        "daniel_lightrag_mcp.http_server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
