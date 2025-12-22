"""
Unit tests for LightRAG client functionality.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from daniel_lightrag_mcp.client import (
    LightRAGClient,
    LightRAGError,
    LightRAGConnectionError,
    LightRAGAuthError,
    LightRAGValidationError,
    LightRAGAPIError,
    LightRAGTimeoutError,
    LightRAGServerError
)
from daniel_lightrag_mcp.models import (
    TextDocument,
    InsertResponse,
    QueryResponse,
    QueryDataResponse,
    DocumentsResponse,
    HealthResponse
)


class TestLightRAGClientInitialization:
    """Test LightRAG client initialization."""
    
    def test_client_initialization_default(self):
        """Test client initialization with default parameters."""
        client = LightRAGClient()
        
        assert client.base_url == "http://localhost:9621"
        assert client.api_key is None
        assert client.timeout == 300.0
        assert client.client is not None
    
    def test_client_initialization_custom(self):
        """Test client initialization with custom parameters."""
        client = LightRAGClient(
            base_url="http://custom:8080",
            api_key="test_key",
            timeout=60.0
        )
        
        assert client.base_url == "http://custom:8080"
        assert client.api_key == "test_key"
        assert client.timeout == 60.0
    
    def test_client_initialization_with_api_key(self):
        """Test client initialization with API key sets headers."""
        client = LightRAGClient(api_key="test_key")
        
        # Check that the API key is set in headers
        assert "X-API-Key" in client.client.headers
        assert client.client.headers["X-API-Key"] == "test_key"


class TestErrorMapping:
    """Test HTTP error mapping to custom exceptions."""
    
    def test_map_http_error_400(self):
        """Test mapping of 400 Bad Request."""
        client = LightRAGClient()
        error = client._map_http_error(400, "Bad request", {"detail": "Invalid input"})
        
        assert isinstance(error, LightRAGValidationError)
        assert error.status_code == 400
        assert "Bad Request" in str(error)
    
    def test_map_http_error_401(self):
        """Test mapping of 401 Unauthorized."""
        client = LightRAGClient()
        error = client._map_http_error(401, "Unauthorized")
        
        assert isinstance(error, LightRAGAuthError)
        assert error.status_code == 401
        assert "Unauthorized" in str(error)
    
    def test_map_http_error_404(self):
        """Test mapping of 404 Not Found."""
        client = LightRAGClient()
        error = client._map_http_error(404, "Not found")
        
        assert isinstance(error, LightRAGAPIError)
        assert error.status_code == 404
        assert "Not Found" in str(error)
    
    def test_map_http_error_500(self):
        """Test mapping of 500 Internal Server Error."""
        client = LightRAGClient()
        error = client._map_http_error(500, "Internal server error")
        
        assert isinstance(error, LightRAGServerError)
        assert error.status_code == 500
        assert "Server Error" in str(error)
    
    def test_map_http_error_with_json_detail(self):
        """Test error mapping with JSON detail in response."""
        client = LightRAGClient()
        response_data = {"detail": "Validation failed for field 'text'"}
        error = client._map_http_error(422, json.dumps(response_data), response_data)
        
        assert isinstance(error, LightRAGValidationError)
        assert "Validation failed for field 'text'" in str(error)


@pytest.mark.asyncio
class TestDocumentManagementMethods:
    """Test document management client methods."""

    async def test_insert_text_success(self, lightrag_client, mock_response, sample_insert_response):
        """Test successful text insertion."""
        # Setup mock
        response = mock_response(200, sample_insert_response)
        lightrag_client.client.post = AsyncMock(return_value=response)

        # Execute
        result = await lightrag_client.insert_text("test content", title="Test Title")

        # Verify
        assert isinstance(result, InsertResponse)
        assert result.status == "success"
        assert result.track_id == "track_123"

        # Verify API call
        lightrag_client.client.post.assert_called_once()
        call_args = lightrag_client.client.post.call_args
        assert call_args[0][0] == "http://localhost:9621/documents/text"

        # Verify request data (file_source gets .txt extension)
        request_data = call_args[1]["json"]
        assert request_data["text"] == "test content"
        assert request_data["file_source"] == "Test Title.txt"
    
    async def test_insert_text_empty_content(self, lightrag_client, mock_response, sample_insert_response):
        """Test text insertion with empty content (should be allowed)."""
        # Setup mock
        response = mock_response(200, sample_insert_response)
        lightrag_client.client.post = AsyncMock(return_value=response)
        
        # Execute - empty content should be allowed
        result = await lightrag_client.insert_text("")
        
        # Verify
        assert isinstance(result, InsertResponse)
        lightrag_client.client.post.assert_called_once()
    
    async def test_insert_texts_success(self, lightrag_client, mock_response, sample_insert_response):
        """Test successful multiple text insertion."""
        # Setup mock
        response = mock_response(200, sample_insert_response)
        lightrag_client.client.post = AsyncMock(return_value=response)
        
        # Create test documents
        texts = [
            TextDocument(content="Text 1", title="Title 1"),
            TextDocument(content="Text 2", title="Title 2")
        ]
        
        # Execute
        result = await lightrag_client.insert_texts(texts)
        
        # Verify
        assert isinstance(result, InsertResponse)
        lightrag_client.client.post.assert_called_once()
    
    async def test_upload_document_success(self, lightrag_client, mock_response):
        """Test successful document upload."""
        # Setup mock - new API format
        upload_response = {"status": "uploaded", "message": "File uploaded successfully", "track_id": "track_upload"}
        response = mock_response(200, upload_response)
        lightrag_client.client.post = AsyncMock(return_value=response)

        # Mock file operations
        with patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=True), \
             patch('os.path.getsize', return_value=1024), \
             patch('builtins.open', create=True) as mock_open:

            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            # Execute
            result = await lightrag_client.upload_document("/path/to/test.txt")

            # Verify
            assert result.status == "uploaded"
            assert result.track_id == "track_upload"
            lightrag_client.client.post.assert_called_once()
    
    async def test_upload_document_file_not_found(self, lightrag_client):
        """Test document upload with file not found."""
        with patch('os.path.exists', return_value=False):
            with pytest.raises(LightRAGValidationError, match="File not found"):
                await lightrag_client.upload_document("/nonexistent/file.txt")
    
    async def test_scan_documents_success(self, lightrag_client, mock_response):
        """Test successful document scanning."""
        # Setup mock - new API format
        scan_response = {"status": "success", "message": "Scan completed", "track_id": "scan_123", "new_documents": ["doc1.txt", "doc2.txt"]}
        response = mock_response(200, scan_response)
        lightrag_client.client.post = AsyncMock(return_value=response)

        # Execute
        result = await lightrag_client.scan_documents()

        # Verify
        assert result.status == "success"
        assert len(result.new_documents) == 2
        lightrag_client.client.post.assert_called_once_with(
            "http://localhost:9621/documents/scan", json=None
        )

    # Note: get_documents test is removed since the tool is deprecated in the API
    # Use get_documents_paginated instead

    async def test_get_documents_paginated_success(self, lightrag_client, mock_response):
        """Test successful paginated document retrieval."""
        # Setup mock
        paginated_response = {
            "documents": [{"id": "doc_123", "title": "Test", "status": "processed"}],
            "pagination": {"page": 1, "page_size": 10, "total_pages": 1, "total_items": 1}
        }
        response = mock_response(200, paginated_response)
        lightrag_client.client.post = AsyncMock(return_value=response)
        
        # Execute
        result = await lightrag_client.get_documents_paginated(page=1, page_size=10)
        
        # Verify
        assert len(result.documents) == 1
        assert result.pagination.page == 1
        assert result.pagination.page_size == 10
        lightrag_client.client.post.assert_called_once()
    
    async def test_delete_document_success(self, lightrag_client, mock_response):
        """Test successful single document deletion (backward compatibility)."""
        # Setup mock - new API format
        delete_response = {"status": "success", "message": "Document deleted", "doc_id": "doc_123"}
        response = mock_response(200, delete_response)
        lightrag_client.client.delete = AsyncMock(return_value=response)

        # Execute
        result = await lightrag_client.delete_document("doc_123")

        # Verify
        assert result.status == "success"
        assert result.doc_id == "doc_123"
        lightrag_client.client.delete.assert_called_once()

    async def test_delete_documents_batch_success(self, lightrag_client, mock_response):
        """Test successful batch document deletion."""
        # Setup mock - new API format
        delete_response = {"status": "success", "message": "Documents deleted", "track_id": "delete_batch"}
        response = mock_response(200, delete_response)
        lightrag_client.client.delete = AsyncMock(return_value=response)

        # Execute
        result = await lightrag_client.delete_document(["doc_1", "doc_2", "doc_3"])

        # Verify
        assert result.status == "success"
        lightrag_client.client.delete.assert_called_once()

    async def test_delete_document_with_options(self, lightrag_client, mock_response):
        """Test document deletion with file and cache deletion options."""
        # Setup mock - new API format
        delete_response = {"status": "success", "message": "Document deleted", "doc_id": "doc_123"}
        response = mock_response(200, delete_response)
        lightrag_client.client.delete = AsyncMock(return_value=response)

        # Execute
        result = await lightrag_client.delete_document(
            "doc_123",
            delete_file=True,
            delete_llm_cache=True
        )

        # Verify
        assert result.status == "success"
        assert result.doc_id == "doc_123"
        lightrag_client.client.delete.assert_called_once()

    async def test_clear_documents_success(self, lightrag_client, mock_response):
        """Test successful document clearing."""
        # Setup mock - new API format
        clear_response = {"status": "success", "message": "All documents cleared"}
        response = mock_response(200, clear_response)
        lightrag_client.client.delete = AsyncMock(return_value=response)

        # Execute
        result = await lightrag_client.clear_documents()

        # Verify
        assert result.status == "success"
        assert result.message == "All documents cleared"
        lightrag_client.client.delete.assert_called_once_with(
            "http://localhost:9621/documents"
        )


@pytest.mark.asyncio
class TestQueryMethods:
    """Test query client methods."""

    async def test_query_text_success(self, lightrag_client, mock_response, sample_query_response):
        """Test successful text query (new format with references)."""
        # Setup mock
        response = mock_response(200, sample_query_response)
        lightrag_client.client.post = AsyncMock(return_value=response)

        # Execute
        result = await lightrag_client.query_text("test query", mode="mix", only_need_context=False)

        # Verify
        assert isinstance(result, QueryResponse)
        assert "AI-generated answer" in result.response
        assert len(result.references) == 2
        assert result.references[0].reference_id == "1"
        assert result.references[0].file_path == "/documents/ai_overview.pdf"

        # Verify API call
        lightrag_client.client.post.assert_called_once()
        call_args = lightrag_client.client.post.call_args
        assert call_args[0][0] == "http://localhost:9621/query"

        # Verify request data
        request_data = call_args[1]["json"]
        assert request_data["query"] == "test query"
        assert request_data["mode"] == "mix"
        assert request_data["only_need_context"] is False

    async def test_query_text_with_bypass_mode(self, lightrag_client, mock_response):
        """Test query with bypass mode."""
        # Setup mock
        bypass_response = {"response": "Bypass response"}
        response = mock_response(200, bypass_response)
        lightrag_client.client.post = AsyncMock(return_value=response)

        # Execute
        result = await lightrag_client.query_text("test query", mode="bypass")

        # Verify
        assert result.response == "Bypass response"
        lightrag_client.client.post.assert_called_once()

    async def test_query_text_validation_error_empty_query(self, lightrag_client):
        """Test query with empty query string."""
        with pytest.raises(LightRAGValidationError, match="Query cannot be empty"):
            await lightrag_client.query_text("")

    async def test_query_text_validation_error_invalid_mode(self, lightrag_client):
        """Test query with invalid mode."""
        with pytest.raises(LightRAGValidationError, match="Invalid query mode"):
            await lightrag_client.query_text("test query", mode="invalid_mode")

    async def test_query_text_stream_success(self, lightrag_client, mock_streaming_response):
        """Test successful streaming text query."""
        # Setup mock
        chunks = ["chunk 1", "chunk 2", "chunk 3"]
        streaming_response = mock_streaming_response(chunks)

        # Mock the stream context manager
        mock_stream_context = AsyncMock()
        mock_stream_context.__aenter__ = AsyncMock(return_value=streaming_response)
        mock_stream_context.__aexit__ = AsyncMock(return_value=None)
        lightrag_client.client.stream = MagicMock(return_value=mock_stream_context)

        # Execute and collect results
        results = []
        async for chunk in lightrag_client.query_text_stream("test query", mode="mix"):
            results.append(chunk)

        # Verify
        assert results == chunks
        # Verify the call was made with correct endpoint
        lightrag_client.client.stream.assert_called_once()
        call_args = lightrag_client.client.stream.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "http://localhost:9621/query/stream"
        # Verify essential params in request
        request_json = call_args[1]["json"]
        assert request_json["query"] == "test query"
        assert request_json["mode"] == "mix"
        assert request_json["stream"] is True

    async def test_query_text_stream_validation_error(self, lightrag_client):
        """Test streaming query with validation error."""
        with pytest.raises(LightRAGValidationError, match="Query cannot be empty"):
            async for _ in lightrag_client.query_text_stream(""):
                pass

    async def test_query_data_success(self, lightrag_client, mock_response, sample_query_data_response):
        """Test successful query_data call."""
        # Setup mock
        response = mock_response(200, sample_query_data_response)
        lightrag_client.client.post = AsyncMock(return_value=response)

        # Execute
        result = await lightrag_client.query_data("what are neural networks", mode="local")

        # Verify
        from daniel_lightrag_mcp.models import QueryDataResponse
        assert isinstance(result, QueryDataResponse)
        assert result.status == "success"
        assert len(result.data.entities) == 1
        assert result.data.entities[0].entity_name == "Neural Networks"
        assert len(result.data.relationships) == 1
        assert result.data.relationships[0].src_id == "Neural Networks"
        assert len(result.data.chunks) == 1
        assert result.metadata.query_mode == "local"

        # Verify API call was made to correct endpoint
        lightrag_client.client.post.assert_called_once()
        call_args = lightrag_client.client.post.call_args
        assert call_args[0][0] == "http://localhost:9621/query/data"
        request_json = call_args[1]["json"]
        assert request_json["query"] == "what are neural networks"
        assert request_json["mode"] == "local"
        assert request_json["stream"] is False

    async def test_query_data_with_all_params(self, lightrag_client, mock_response, sample_query_data_response):
        """Test query_data with all parameters."""
        # Setup mock
        response = mock_response(200, sample_query_data_response)
        lightrag_client.client.post = AsyncMock(return_value=response)

        # Execute
        result = await lightrag_client.query_data(
            query="test query",
            mode="mix",
            top_k=10,
            chunk_top_k=20,
            max_entity_tokens=1000,
            max_relation_tokens=2000,
            max_total_tokens=5000,
            hl_keywords=["AI", "ML"],
            ll_keywords=["neural", "network"],
            enable_rerank=False,
            conversation_history=[{"role": "user", "content": "previous question"}]
        )

        # Verify
        assert result.status == "success"
        lightrag_client.client.post.assert_called_once()

        # Verify request data
        call_args = lightrag_client.client.post.call_args
        request_data = call_args[1]["json"]
        assert request_data["query"] == "test query"
        assert request_data["mode"] == "mix"
        assert request_data["top_k"] == 10
        assert request_data["chunk_top_k"] == 20
        assert request_data["hl_keywords"] == ["AI", "ML"]
        assert request_data["ll_keywords"] == ["neural", "network"]

    async def test_query_data_validation_error_empty_query(self, lightrag_client):
        """Test query_data with empty query string."""
        with pytest.raises(LightRAGValidationError, match="Query cannot be empty"):
            await lightrag_client.query_data("")

    async def test_query_data_validation_error_invalid_mode(self, lightrag_client):
        """Test query_data with invalid mode."""
        with pytest.raises(LightRAGValidationError, match="Invalid query mode"):
            await lightrag_client.query_data("test query", mode="invalid")


@pytest.mark.asyncio
class TestKnowledgeGraphMethods:
    """Test knowledge graph client methods."""

    async def test_get_knowledge_graph_success(self, lightrag_client, mock_response, sample_graph_response):
        """Test successful knowledge graph retrieval."""
        # Setup mock - API returns nodes/edges directly
        response = mock_response(200, sample_graph_response)
        lightrag_client.client.get = AsyncMock(return_value=response)

        # Execute
        result = await lightrag_client.get_knowledge_graph()

        # Verify - API returns nodes/edges, model stores them directly
        assert len(result.nodes) == 1
        assert len(result.edges) == 1
        assert result.nodes[0]["id"] == "entity_123"
        assert result.edges[0]["id"] == "rel_123"
        lightrag_client.client.get.assert_called_once_with(
            "http://localhost:9621/graphs", params={"label": "*"}
        )
    
    async def test_get_graph_labels_success(self, lightrag_client, mock_response):
        """Test successful graph labels retrieval."""
        # Setup mock
        labels_response = {
            "entity_labels": ["Person", "Organization"],
            "relation_labels": ["works_for", "located_in"]
        }
        response = mock_response(200, labels_response)
        lightrag_client.client.get = AsyncMock(return_value=response)
        
        # Execute
        result = await lightrag_client.get_graph_labels()
        
        # Verify
        assert len(result.entity_labels) == 2
        assert len(result.relation_labels) == 2
        assert "Person" in result.entity_labels
        assert "works_for" in result.relation_labels
        lightrag_client.client.get.assert_called_once_with(
            "http://localhost:9621/graph/label/list", params=None
        )
    
    async def test_check_entity_exists_success(self, lightrag_client, mock_response):
        """Test successful entity existence check."""
        # Setup mock
        exists_response = {"exists": True, "entity_name": "Test Entity", "entity_id": "ent_123"}
        response = mock_response(200, exists_response)
        lightrag_client.client.get = AsyncMock(return_value=response)

        # Execute
        result = await lightrag_client.check_entity_exists("Test Entity")

        # Verify
        assert result.exists is True
        assert result.entity_name == "Test Entity"
        assert result.entity_id == "ent_123"
        lightrag_client.client.get.assert_called_once_with(
            "http://localhost:9621/graph/entity/exists",
            params={"name": "Test Entity"}
        )

    async def test_update_entity_success(self, lightrag_client, mock_response):
        """Test successful entity update."""
        # Setup mock - new API format
        update_response = {"status": "success", "message": "Entity updated", "data": {"entity_name": "Updated Entity"}}
        response = mock_response(200, update_response)
        lightrag_client.client.post = AsyncMock(return_value=response)

        # Execute
        updated_data = {"description": "Updated description"}
        result = await lightrag_client.update_entity("Test Entity", updated_data)

        # Verify
        assert result.status == "success"
        lightrag_client.client.post.assert_called_once()

        # Verify request data
        call_args = lightrag_client.client.post.call_args
        request_data = call_args[1]["json"]
        assert request_data["entity_name"] == "Test Entity"
        assert request_data["updated_data"] == updated_data

    async def test_update_relation_success(self, lightrag_client, mock_response):
        """Test successful relation update."""
        # Setup mock - new API format
        update_response = {"status": "success", "message": "Relation updated", "data": {"src_id": "A", "tgt_id": "B"}}
        response = mock_response(200, update_response)
        lightrag_client.client.post = AsyncMock(return_value=response)

        # Execute
        updated_data = {"weight": 0.9}
        result = await lightrag_client.update_relation("Entity A", "Entity B", updated_data)

        # Verify
        assert result.status == "success"
        lightrag_client.client.post.assert_called_once()
    
    async def test_delete_entity_success(self, lightrag_client, mock_response):
        """Test successful entity deletion."""
        # Setup mock - new API format
        delete_response = {"status": "success", "doc_id": "ent_123", "message": "Entity deleted", "status_code": 200}
        response = mock_response(200, delete_response)
        lightrag_client.client.delete = AsyncMock(return_value=response)

        # Execute
        result = await lightrag_client.delete_entity("Test Entity")

        # Verify
        assert result.status == "success"
        assert result.doc_id == "ent_123"
        lightrag_client.client.delete.assert_called_once()

    async def test_delete_relation_success(self, lightrag_client, mock_response):
        """Test successful relation deletion."""
        # Setup mock - new API format
        delete_response = {"status": "success", "doc_id": "rel_123", "message": "Relation deleted", "status_code": 200}
        response = mock_response(200, delete_response)
        lightrag_client.client.delete = AsyncMock(return_value=response)

        # Execute
        result = await lightrag_client.delete_relation("Entity A", "Entity B")

        # Verify
        assert result.status == "success"
        assert result.doc_id == "rel_123"
        lightrag_client.client.delete.assert_called_once()

    async def test_get_popular_labels_success(self, lightrag_client, mock_response, sample_popular_labels_response):
        """Test successful popular labels retrieval."""
        # Setup mock - API returns list directly
        response = mock_response(200, sample_popular_labels_response)
        lightrag_client.client.get = AsyncMock(return_value=response)

        # Execute
        result = await lightrag_client.get_popular_labels(limit=10)

        # Verify
        assert len(result.labels) == 5
        assert result.labels[0] == "人工智能"
        assert "机器学习" in result.labels
        lightrag_client.client.get.assert_called_once_with(
            "http://localhost:9621/graph/label/popular", params={"limit": 10}
        )

    async def test_get_popular_labels_default_limit(self, lightrag_client, mock_response, sample_popular_labels_response):
        """Test popular labels with default limit."""
        # Setup mock
        response = mock_response(200, sample_popular_labels_response)
        lightrag_client.client.get = AsyncMock(return_value=response)

        # Execute
        result = await lightrag_client.get_popular_labels()

        # Verify - default limit is 300
        lightrag_client.client.get.assert_called_once_with(
            "http://localhost:9621/graph/label/popular", params={"limit": 300}
        )

    async def test_get_popular_labels_limit_bounds(self, lightrag_client, mock_response):
        """Test popular labels limit bounds."""
        # Test too low limit
        response = mock_response(200, [])
        lightrag_client.client.get = AsyncMock(return_value=response)
        await lightrag_client.get_popular_labels(limit=0)
        lightrag_client.client.get.assert_called_with(
            "http://localhost:9621/graph/label/popular", params={"limit": 1}
        )

    async def test_search_labels_success(self, lightrag_client, mock_response, sample_search_labels_response):
        """Test successful label search."""
        # Setup mock - API returns list directly
        response = mock_response(200, sample_search_labels_response)
        lightrag_client.client.get = AsyncMock(return_value=response)

        # Execute
        result = await lightrag_client.search_labels("AI", limit=10)

        # Verify
        assert len(result.labels) == 3
        assert "人工智能" in result.labels
        assert "AIGC" in result.labels
        lightrag_client.client.get.assert_called_once_with(
            "http://localhost:9621/graph/label/search", params={"q": "AI", "limit": 10}
        )

    async def test_search_labels_default_limit(self, lightrag_client, mock_response, sample_search_labels_response):
        """Test search labels with default limit."""
        # Setup mock
        response = mock_response(200, sample_search_labels_response)
        lightrag_client.client.get = AsyncMock(return_value=response)

        # Execute
        result = await lightrag_client.search_labels("AI")

        # Verify - default limit is 50
        lightrag_client.client.get.assert_called_once_with(
            "http://localhost:9621/graph/label/search", params={"q": "AI", "limit": 50}
        )

    async def test_search_labels_empty_query(self, lightrag_client):
        """Test search labels with empty query."""
        with pytest.raises(LightRAGValidationError, match="Search query cannot be empty"):
            await lightrag_client.search_labels("")

    async def test_search_labels_whitespace_query(self, lightrag_client):
        """Test search labels with whitespace-only query."""
        with pytest.raises(LightRAGValidationError, match="Search query cannot be empty"):
            await lightrag_client.search_labels("   ")


@pytest.mark.asyncio
class TestSystemManagementMethods:
    """Test system management client methods."""

    async def test_get_pipeline_status_success(self, lightrag_client, mock_response, sample_pipeline_status_response):
        """Test successful pipeline status retrieval."""
        # Setup mock - new API format includes more fields
        full_pipeline_response = {
            "status": "running",
            "progress": 75.5,
            "current_task": "processing documents",
            "message": "Pipeline is running normally",
            "autoscanned": True,
            "busy": True,
            "job_name": "ingest_job",
            "docs": 100,
            "batchs": 5,
            "cur_batch": 3,
            "request_pending": False,
            "latest_message": "Processing batch 3"
        }
        response = mock_response(200, full_pipeline_response)
        lightrag_client.client.get = AsyncMock(return_value=response)

        # Execute
        result = await lightrag_client.get_pipeline_status()

        # Verify
        assert result.autoscanned is True
        assert result.busy is True
        assert result.progress == 75.5
        assert result.current_task == "processing documents"
        lightrag_client.client.get.assert_called_once_with(
            "http://localhost:9621/documents/pipeline_status", params=None
        )

    async def test_get_track_status_success(self, lightrag_client, mock_response):
        """Test successful track status retrieval."""
        # Setup mock - new API format
        track_response = {
            "track_id": "track_123",
            "documents": [{"id": "doc_1", "status": "processed"}],
            "total_count": 1,
            "status_summary": {"processed": 1}
        }
        response = mock_response(200, track_response)
        lightrag_client.client.get = AsyncMock(return_value=response)

        # Execute
        result = await lightrag_client.get_track_status("track_123")

        # Verify
        assert result.track_id == "track_123"
        assert len(result.documents) == 1
        lightrag_client.client.get.assert_called_once_with(
            "http://localhost:9621/documents/track_status/track_123", params=None
        )

    async def test_get_document_status_counts_success(self, lightrag_client, mock_response, sample_status_counts_response):
        """Test successful document status counts retrieval."""
        # Setup mock - new API format returns status_counts object
        status_response = {"status_counts": sample_status_counts_response}
        response = mock_response(200, status_response)
        lightrag_client.client.get = AsyncMock(return_value=response)

        # Execute
        result = await lightrag_client.get_document_status_counts()

        # Verify - status_counts is a dict, access by key
        assert result.status_counts["pending"] == 5
        assert result.status_counts["processing"] == 2
        assert result.status_counts["processed"] == 100
        assert result.status_counts["failed"] == 1
        lightrag_client.client.get.assert_called_once_with(
            "http://localhost:9621/documents/status_counts", params=None
        )

    async def test_clear_cache_success(self, lightrag_client, mock_response):
        """Test successful cache clearing."""
        # Setup mock - new API format
        cache_response = {"status": "success", "message": "Cache cleared", "cache_type": "all"}
        response = mock_response(200, cache_response)
        lightrag_client.client.post = AsyncMock(return_value=response)

        # Execute
        result = await lightrag_client.clear_cache()

        # Verify
        assert result.status == "success"
        assert result.cache_type == "all"
        lightrag_client.client.post.assert_called_once()

    async def test_clear_cache_with_type_success(self, lightrag_client, mock_response):
        """Test successful cache clearing with specific type."""
        # Setup mock - new API format
        cache_response = {"status": "success", "message": "Query cache cleared", "cache_type": "query"}
        response = mock_response(200, cache_response)
        lightrag_client.client.post = AsyncMock(return_value=response)

        # Execute
        result = await lightrag_client.clear_cache(cache_type="query")

        # Verify
        assert result.status == "success"
        assert result.cache_type == "query"
        lightrag_client.client.post.assert_called_once()

        # Verify request data
        call_args = lightrag_client.client.post.call_args
        request_data = call_args[1]["json"]
        assert request_data["cache_type"] == "query"
    
    async def test_get_health_success(self, lightrag_client, mock_response, sample_health_response):
        """Test successful health check."""
        # Setup mock
        response = mock_response(200, sample_health_response)
        lightrag_client.client.get = AsyncMock(return_value=response)
        
        # Execute
        result = await lightrag_client.get_health()
        
        # Verify
        assert isinstance(result, HealthResponse)
        assert result.status == "healthy"
        assert result.version == "1.0.0"
        assert result.uptime == 3600.0
        assert result.database_status == "connected"
        lightrag_client.client.get.assert_called_once_with(
            "http://localhost:9621/health", params=None
        )


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling in client methods."""
    
    async def test_http_status_error_handling(self, lightrag_client, mock_response):
        """Test handling of HTTP status errors."""
        # Setup mock to raise HTTP error
        response = mock_response(400, {"detail": "Bad request"}, "Bad request")
        lightrag_client.client.get = AsyncMock(return_value=response)
        
        # Execute and verify error
        with pytest.raises(LightRAGValidationError, match="Bad Request"):
            await lightrag_client.get_health()
    
    async def test_connection_error_handling(self, lightrag_client):
        """Test handling of connection errors."""
        # Setup mock to raise connection error
        lightrag_client.client.get = AsyncMock(
            side_effect=httpx.ConnectError("Connection failed")
        )
        
        # Execute and verify error
        with pytest.raises(LightRAGConnectionError, match="Connection failed"):
            await lightrag_client.get_health()
    
    async def test_timeout_error_handling(self, lightrag_client):
        """Test handling of timeout errors."""
        # Setup mock to raise timeout error
        lightrag_client.client.get = AsyncMock(
            side_effect=httpx.TimeoutException("Request timeout")
        )
        
        # Execute and verify error
        with pytest.raises(LightRAGTimeoutError, match="Request timeout"):
            await lightrag_client.get_health()
    
    async def test_json_decode_error_handling(self, lightrag_client):
        """Test handling of JSON decode errors."""
        # Setup mock with invalid JSON response
        response = MagicMock()
        response.status_code = 200
        response.raise_for_status = MagicMock()
        response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        response.text = "Invalid JSON response"
        response.headers = {}  # Add proper headers mock
        
        lightrag_client.client.get = AsyncMock(return_value=response)
        
        # Execute and verify error (it will be wrapped in LightRAGError due to exception handling)
        with pytest.raises(LightRAGError, match="Invalid JSON response"):
            await lightrag_client.get_health()
    
    async def test_streaming_error_handling(self, lightrag_client):
        """Test error handling in streaming requests."""
        # Setup mock to raise HTTP error in streaming
        mock_stream_context = AsyncMock()
        mock_stream_context.__aenter__ = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                message="HTTP 500",
                request=MagicMock(),
                response=MagicMock(status_code=500, text="Server error")
            )
        )
        lightrag_client.client.stream = MagicMock(return_value=mock_stream_context)
        
        # Execute and verify error
        with pytest.raises(LightRAGServerError, match="Server Error"):
            async for _ in lightrag_client.query_text_stream("test query"):
                pass


@pytest.mark.asyncio
class TestContextManager:
    """Test client context manager functionality."""
    
    async def test_context_manager_usage(self):
        """Test client can be used as async context manager."""
        async with LightRAGClient() as client:
            assert client.client is not None
        
        # Client should be closed after context exit
        # Note: We can't easily test this without mocking the httpx client
    
    async def test_manual_close(self):
        """Test manual client closing."""
        client = LightRAGClient()
        
        # Mock the httpx client close method
        client.client.aclose = AsyncMock()
        
        # Close the client
        await client.__aexit__(None, None, None)
        
        # Verify close was called
        client.client.aclose.assert_called_once()