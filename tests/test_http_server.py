"""
Tests for the HTTP server functionality.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

from daniel_lightrag_mcp.http_server import app, clients, get_client
from daniel_lightrag_mcp.client import LightRAGClient


@pytest.fixture
def mock_lightrag_client():
    """Create a mock LightRAG client."""
    client = AsyncMock(spec=LightRAGClient)

    # Mock common responses
    client.get_health.return_value = {"status": "healthy", "version": "1.0"}
    client.query_text.return_value = MagicMock(
        response="This is a test response",
        results=[]
    )
    client.insert_text.return_value = {"track_id": "test-track-123"}
    client.get_documents_paginated.return_value = MagicMock(
        documents=[],
        total=0,
        page=1,
        page_size=20
    )

    return client


@pytest.fixture
def test_client(mock_lightrag_client):
    """Create a test client with mocked dependencies."""
    # Clear any existing clients
    clients.clear()

    # Add test client
    clients["test_prefix"] = mock_lightrag_client
    clients["default"] = mock_lightrag_client

    # Patch both _remove_tool_prefix and _validate_tool_arguments
    with patch("daniel_lightrag_mcp.http_server._remove_tool_prefix") as mock_remove, \
         patch("daniel_lightrag_mcp.http_server._validate_tool_arguments") as mock_validate:

        # Return the tool name without prefix
        mock_remove.side_effect = lambda name: name.replace("test_prefix_", "") if name.startswith("test_prefix_") else name

        # Don't raise validation errors in tests
        mock_validate.return_value = None

        # Create test client
        yield TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, test_client):
        """Test health check returns correct status."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "prefixes" in data
        assert "version" in data


class TestListToolsEndpoint:
    """Tests for list tools endpoint."""

    def test_list_tools_with_prefix(self, test_client):
        """Test listing tools for a specific prefix."""
        with patch("daniel_lightrag_mcp.http_server.handle_list_tools", new_callable=AsyncMock) as mock_handle:
            # Mock tool list with prefixed tools
            mock_tool = MagicMock()
            mock_tool.name = "test_prefix_query_text"
            mock_tool.description = "[test_prefix] Query LightRAG with text"
            mock_tool.inputSchema = {"type": "object", "properties": {}}

            # Set return value for async mock
            mock_handle.return_value = [mock_tool]

            response = test_client.get("/mcp/test_prefix/tools")

            assert response.status_code == 200
            data = response.json()
            assert data["prefix"] == "test_prefix"
            assert "tools" in data
            assert "count" in data

    def test_list_tools_empty_prefix(self, test_client):
        """Test listing tools with no matching prefix."""
        with patch("daniel_lightrag_mcp.http_server.handle_list_tools", new_callable=AsyncMock) as mock_handle:
            # Set return value for async mock
            mock_handle.return_value = []

            response = test_client.get("/mcp/nonexistent_prefix/tools")

            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 0


class TestExecuteToolEndpoint:
    """Tests for execute tool endpoint."""

    def test_execute_query_text_tool(self, test_client, mock_lightrag_client):
        """Test executing query_text tool."""
        response = test_client.post(
            "/mcp/test_prefix/test_prefix_query_text",
            json={
                "arguments": {
                    "query": "What is the answer?",
                    "mode": "hybrid"
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

        # Verify client was called
        mock_lightrag_client.query_text.assert_called_once()

    def test_execute_insert_text_tool(self, test_client, mock_lightrag_client):
        """Test executing insert_text tool."""
        response = test_client.post(
            "/mcp/test_prefix/test_prefix_insert_text",
            json={
                "arguments": {
                    "text": "This is a test document"
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify client was called
        mock_lightrag_client.insert_text.assert_called_once_with("This is a test document")

    def test_execute_get_health_tool(self, test_client, mock_lightrag_client):
        """Test executing get_health tool."""
        response = test_client.post(
            "/mcp/test_prefix/test_prefix_get_health",
            json={"arguments": {}}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify client was called
        mock_lightrag_client.get_health.assert_called_once()

    def test_prefix_mismatch_error(self, test_client):
        """Test error when tool name doesn't match prefix."""
        response = test_client.post(
            "/mcp/test_prefix/wrong_prefix_query_text",
            json={"arguments": {"query": "test"}}
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "does not match prefix" in data["error"]

    def test_unknown_tool_error(self, test_client):
        """Test error when tool doesn't exist."""
        response = test_client.post(
            "/mcp/test_prefix/test_prefix_nonexistent_tool",
            json={"arguments": {}}
        )

        assert response.status_code == 404

    def test_missing_arguments_error(self, test_client):
        """Test error when required arguments are missing."""
        response = test_client.post(
            "/mcp/test_prefix/test_prefix_query_text",
            json={"arguments": {}}  # Missing 'query' argument
        )

        assert response.status_code == 500  # Validation error


class TestStreamingEndpoint:
    """Tests for streaming tool execution."""

    @pytest.mark.asyncio
    async def test_streaming_query(self, mock_lightrag_client):
        """Test streaming query response."""
        # Mock streaming response
        async def mock_stream():
            yield "First chunk"
            yield "Second chunk"
            yield "Third chunk"

        mock_lightrag_client.query_text_stream.return_value = mock_stream()

        # Patch functions for streaming test
        with patch("daniel_lightrag_mcp.http_server._remove_tool_prefix") as mock_remove, \
             patch("daniel_lightrag_mcp.http_server._validate_tool_arguments") as mock_validate:

            mock_remove.side_effect = lambda name: name.replace("test_prefix_", "") if name.startswith("test_prefix_") else name
            mock_validate.return_value = None

            # Set up mock client
            clients["test_prefix"] = mock_lightrag_client

            # Use TestClient which can handle streaming responses
            client = TestClient(app)

            response = client.post(
                "/mcp/test_prefix/test_prefix_query_text_stream",
                json={
                    "arguments": {
                        "query": "Stream this",
                        "mode": "hybrid"
                    },
                    "stream": True
                }
            )

            assert response.status_code == 200
            assert "application/x-ndjson" in response.headers["content-type"]

            # Parse NDJSON response
            chunks = []
            for line in response.text.strip().split("\n"):
                if line:
                    data = json.loads(line)
                    chunks.append(data)

            # Should have chunks + done message
            assert len(chunks) > 0
            assert any(c["type"] == "chunk" for c in chunks)
            assert chunks[-1]["type"] == "done"


class TestPrefixRouting:
    """Tests for prefix-based routing."""

    def test_get_client_existing_prefix(self, mock_lightrag_client):
        """Test getting client for existing prefix."""
        clients["test_prefix"] = mock_lightrag_client

        client = get_client("test_prefix")
        assert client is mock_lightrag_client

    def test_get_client_default_fallback(self, mock_lightrag_client):
        """Test fallback to default client."""
        clients.clear()
        clients["default"] = mock_lightrag_client

        client = get_client("nonexistent_prefix")
        assert client is mock_lightrag_client

    def test_get_client_no_client_error(self):
        """Test error when no client is configured."""
        clients.clear()

        with pytest.raises(Exception):  # HTTPException
            get_client("nonexistent_prefix")


class TestErrorHandling:
    """Tests for error handling."""

    def test_lightrag_error_handling(self, test_client, mock_lightrag_client):
        """Test handling of LightRAG errors."""
        from daniel_lightrag_mcp.client import LightRAGAPIError

        # Mock an API error
        mock_lightrag_client.query_text.side_effect = LightRAGAPIError(
            "API Error", 500, {}
        )

        response = test_client.post(
            "/mcp/test_prefix/test_prefix_query_text",
            json={
                "arguments": {
                    "query": "This will fail",
                    "mode": "hybrid"
                }
            }
        )

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    def test_validation_error_handling(self, test_client):
        """Test handling of validation errors."""
        response = test_client.post(
            "/mcp/test_prefix/test_prefix_query_text",
            json={
                "arguments": {}  # Missing required 'query' field
            }
        )

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False


class TestClientInitialization:
    """Tests for client initialization."""

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"LIGHTRAG_HTTP_PREFIXES": "prefix1:http://localhost:9621:key1,prefix2:http://localhost:9622:key2"})
    @patch("daniel_lightrag_mcp.http_server.LightRAGClient")
    async def test_initialize_multiple_clients(self, mock_client_class):
        """Test initializing multiple clients from environment."""
        from daniel_lightrag_mcp.http_server import initialize_clients

        clients.clear()
        await initialize_clients()

        # Should have created 2 clients
        assert "prefix1" in clients
        assert "prefix2" in clients
        assert mock_client_class.call_count == 2

    @pytest.mark.asyncio
    @patch.dict("os.environ", {}, clear=True)
    @patch("daniel_lightrag_mcp.http_server.LightRAGClient")
    async def test_initialize_default_client(self, mock_client_class):
        """Test initializing default client when no prefixes configured."""
        from daniel_lightrag_mcp.http_server import initialize_clients

        clients.clear()
        await initialize_clients()

        # Should have default client
        assert "default" in clients
        assert mock_client_class.call_count == 1


class TestResponseFormats:
    """Tests for response formats."""

    def test_regular_response_format(self, test_client, mock_lightrag_client):
        """Test regular JSON response format."""
        response = test_client.post(
            "/mcp/test_prefix/test_prefix_get_health",
            json={"arguments": {}}
        )

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "success" in data
        assert "data" in data or "error" in data

    @pytest.mark.asyncio
    async def test_streaming_response_format(self, mock_lightrag_client):
        """Test NDJSON streaming response format."""
        async def mock_stream():
            yield "chunk1"
            yield "chunk2"

        mock_lightrag_client.query_text_stream.return_value = mock_stream()

        # Patch functions for streaming test
        with patch("daniel_lightrag_mcp.http_server._remove_tool_prefix") as mock_remove, \
             patch("daniel_lightrag_mcp.http_server._validate_tool_arguments") as mock_validate:

            mock_remove.side_effect = lambda name: name.replace("test_prefix_", "") if name.startswith("test_prefix_") else name
            mock_validate.return_value = None

            # Set up mock client
            clients["test_prefix"] = mock_lightrag_client

            # Use TestClient which can handle streaming responses
            client = TestClient(app)

            response = client.post(
                "/mcp/test_prefix/test_prefix_query_text_stream",
                json={
                    "arguments": {"query": "test"},
                    "stream": True
                }
            )

            # Check headers
            assert "application/x-ndjson" in response.headers["content-type"]
            assert response.headers["cache-control"] == "no-cache"

            # Parse NDJSON
            lines = response.text.strip().split("\n")
            for line in lines:
                if line:
                    data = json.loads(line)
                    assert "type" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
