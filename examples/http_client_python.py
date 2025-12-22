"""
Python client examples for LightRAG MCP HTTP Server.
"""

import requests
import json
from typing import Iterator, Dict, Any


class LightRAGHTTPClient:
    """Simple HTTP client for LightRAG MCP Server."""

    def __init__(self, base_url: str = "http://localhost:8000", prefix: str = "default"):
        """
        Initialize the client.

        Args:
            base_url: Base URL of the HTTP server
            prefix: Tool prefix to use
        """
        self.base_url = base_url.rstrip("/")
        self.prefix = prefix

    def _tool_url(self, tool_name: str) -> str:
        """Get full URL for a tool."""
        # Tool name should already include prefix
        if not tool_name.startswith(f"{self.prefix}_"):
            tool_name = f"{self.prefix}_{tool_name}"
        return f"{self.base_url}/mcp/{self.prefix}/{tool_name}"

    def health(self) -> Dict[str, Any]:
        """Check server health."""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def list_tools(self) -> Dict[str, Any]:
        """List all tools for this prefix."""
        response = requests.get(f"{self.base_url}/mcp/{self.prefix}/tools")
        response.raise_for_status()
        return response.json()

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool and return the result.

        Args:
            tool_name: Tool name (without prefix, or with prefix)
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        url = self._tool_url(tool_name)
        response = requests.post(
            url,
            json={"arguments": arguments}
        )
        response.raise_for_status()
        return response.json()

    def execute_tool_stream(self, tool_name: str, arguments: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """
        Execute a tool with streaming response.

        Args:
            tool_name: Tool name
            arguments: Tool arguments

        Yields:
            Streaming chunks as dictionaries
        """
        url = self._tool_url(tool_name)
        response = requests.post(
            url,
            json={"arguments": arguments, "stream": True},
            stream=True
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                yield json.loads(line.decode("utf-8"))

    # Convenient methods for common tools

    def query_text(self, query: str, mode: str = "hybrid") -> str:
        """Query with text."""
        result = self.execute_tool("query_text", {"query": query, "mode": mode})
        return result["data"]["response"]

    def query_text_stream(self, query: str, mode: str = "hybrid") -> Iterator[str]:
        """Query with streaming response."""
        for chunk in self.execute_tool_stream("query_text_stream", {"query": query, "mode": mode}):
            if chunk["type"] == "chunk":
                yield chunk["data"]
            elif chunk["type"] == "error":
                raise Exception(chunk["error"])

    def insert_text(self, text: str) -> Dict[str, Any]:
        """Insert text content."""
        result = self.execute_tool("insert_text", {"text": text})
        return result["data"]

    def insert_texts(self, texts: list) -> Dict[str, Any]:
        """Insert multiple text documents."""
        result = self.execute_tool("insert_texts", {"texts": texts})
        return result["data"]

    def get_documents(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get documents with pagination."""
        result = self.execute_tool("get_documents_paginated", {"page": page, "page_size": page_size})
        return result["data"]

    def get_knowledge_graph(self) -> Dict[str, Any]:
        """Get knowledge graph."""
        result = self.execute_tool("get_knowledge_graph", {})
        return result["data"]


def example_basic_usage():
    """Basic usage example."""
    print("=" * 70)
    print("Example 1: Basic Usage")
    print("=" * 70)

    client = LightRAGHTTPClient(prefix="novel_style")

    # Health check
    health = client.health()
    print(f"Server status: {health['status']}")
    print(f"Available prefixes: {health['prefixes']}\n")

    # List tools
    tools_info = client.list_tools()
    print(f"Tools for prefix '{client.prefix}': {tools_info['count']}")
    print(f"First tool: {tools_info['tools'][0]['name']}\n")

    # Query
    response = client.query_text("What writing techniques are used?")
    print(f"Query response: {response[:100]}...\n")


def example_streaming():
    """Streaming query example."""
    print("=" * 70)
    print("Example 2: Streaming Query")
    print("=" * 70)

    client = LightRAGHTTPClient(prefix="novel_content")

    print("Streaming query: ", end="", flush=True)
    for chunk in client.query_text_stream("Summarize the main plot"):
        print(chunk, end="", flush=True)
    print("\n")


def example_document_management():
    """Document management example."""
    print("=" * 70)
    print("Example 3: Document Management")
    print("=" * 70)

    client = LightRAGHTTPClient(prefix="novel_content")

    # Insert single document
    result = client.insert_text("Chapter 20: The final confrontation begins...")
    print(f"Inserted document, track_id: {result.get('track_id', 'N/A')}")

    # Insert multiple documents
    docs = [
        {
            "title": "Chapter 21",
            "content": "The hero faces their greatest challenge...",
            "metadata": {"chapter": 21}
        },
        {
            "title": "Chapter 22",
            "content": "Victory comes at a great cost...",
            "metadata": {"chapter": 22}
        }
    ]
    result = client.insert_texts(docs)
    print(f"Inserted {len(docs)} documents")

    # Get documents
    docs_page = client.get_documents(page=1, page_size=10)
    print(f"Total documents: {docs_page.get('total', 'N/A')}")
    print(f"Current page: {docs_page.get('page', 'N/A')}\n")


def example_knowledge_graph():
    """Knowledge graph example."""
    print("=" * 70)
    print("Example 4: Knowledge Graph")
    print("=" * 70)

    client = LightRAGHTTPClient(prefix="novel_style")

    # Get knowledge graph
    graph = client.get_knowledge_graph()
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    print(f"Knowledge graph:")
    print(f"  Nodes: {len(nodes)}")
    print(f"  Edges: {len(edges)}")

    if nodes:
        print(f"\nFirst node: {nodes[0]}")

    if edges:
        print(f"First edge: {edges[0]}\n")


def example_error_handling():
    """Error handling example."""
    print("=" * 70)
    print("Example 5: Error Handling")
    print("=" * 70)

    client = LightRAGHTTPClient(prefix="novel_style")

    try:
        # This will fail - wrong tool name
        client.execute_tool("nonexistent_tool", {})
    except requests.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Response: {e.response.json()}\n")


def example_raw_api_calls():
    """Raw API calls without client wrapper."""
    print("=" * 70)
    print("Example 6: Raw API Calls")
    print("=" * 70)

    base_url = "http://localhost:8000"
    prefix = "novel_style"

    # Health check
    response = requests.get(f"{base_url}/health")
    print(f"Health: {response.json()}")

    # Execute tool directly
    response = requests.post(
        f"{base_url}/mcp/{prefix}/{prefix}_query_text",
        json={
            "arguments": {
                "query": "What is the author's style?",
                "mode": "hybrid"
            }
        }
    )
    result = response.json()
    print(f"Success: {result['success']}")
    print(f"Response length: {len(result['data']['response'])} chars\n")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("LightRAG MCP HTTP Client Examples")
    print("=" * 70 + "\n")

    print("Note: Make sure the HTTP server is running:")
    print("  daniel-lightrag-http\n")

    try:
        example_basic_usage()
        # example_streaming()  # Uncomment if streaming endpoint is available
        # example_document_management()  # Uncomment to test
        # example_knowledge_graph()  # Uncomment to test
        example_error_handling()
        example_raw_api_calls()

        print("=" * 70)
        print("All examples completed!")
        print("=" * 70)

    except requests.ConnectionError:
        print("\nError: Could not connect to HTTP server")
        print("Please start the server with: daniel-lightrag-http")
    except Exception as e:
        print(f"\nError: {e}")
