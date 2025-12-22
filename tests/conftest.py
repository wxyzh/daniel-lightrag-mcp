"""
Pytest configuration and fixtures for daniel-lightrag-mcp tests.
"""

import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock
import httpx

from daniel_lightrag_mcp.client import LightRAGClient
from daniel_lightrag_mcp.server import server


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient for testing."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    return mock_client


@pytest.fixture
def lightrag_client(mock_httpx_client):
    """Create a LightRAG client with mocked HTTP client."""
    client = LightRAGClient(base_url="http://localhost:9621")
    client.client = mock_httpx_client
    return client


@pytest.fixture
def mock_response():
    """Create a mock HTTP response."""
    def _create_response(status_code: int = 200, json_data: Dict[str, Any] = None, text: str = ""):
        response = MagicMock()
        response.status_code = status_code
        response.json.return_value = json_data or {}
        response.text = text
        response.raise_for_status = MagicMock()

        if status_code >= 400:
            error = httpx.HTTPStatusError(
                message=f"HTTP {status_code}",
                request=MagicMock(),
                response=response
            )
            response.raise_for_status.side_effect = error

        return response

    return _create_response


@pytest.fixture
def mock_streaming_response():
    """Create a mock streaming HTTP response."""
    def _create_streaming_response(chunks: list, status_code: int = 200):
        async def aiter_text():
            for chunk in chunks:
                yield chunk

        response = MagicMock()
        response.status_code = status_code
        response.aiter_text = aiter_text
        response.raise_for_status = MagicMock()

        if status_code >= 400:
            error = httpx.HTTPStatusError(
                message=f"HTTP {status_code}",
                request=MagicMock(),
                response=response
            )
            response.raise_for_status.side_effect = error

        return response

    return _create_streaming_response


# Sample test data fixtures
@pytest.fixture
def sample_text_document():
    """Sample text document for testing."""
    return {
        "title": "Test Document",
        "content": "This is a test document content.",
        "metadata": {"author": "test", "category": "testing"}
    }


@pytest.fixture
def sample_insert_response():
    """Sample insert response for testing."""
    return {
        "status": "success",
        "message": "Document inserted successfully",
        "track_id": "track_123"
    }


@pytest.fixture
def sample_query_response():
    """Sample query response for testing (new format with references)."""
    return {
        "response": "This is the AI-generated answer to the query.",
        "references": [
            {
                "reference_id": "1",
                "file_path": "/documents/ai_overview.pdf"
            },
            {
                "reference_id": "2",
                "file_path": "/documents/ml_basics.txt"
            }
        ]
    }


@pytest.fixture
def sample_query_data_response():
    """Sample query_data response for testing."""
    return {
        "status": "success",
        "message": "Query executed successfully",
        "data": {
            "entities": [
                {
                    "entity_name": "Neural Networks",
                    "entity_type": "CONCEPT",
                    "description": "Computational models inspired by biological neural networks",
                    "source_id": "chunk-123",
                    "file_path": "/documents/ai_basics.pdf",
                    "reference_id": "1"
                }
            ],
            "relationships": [
                {
                    "src_id": "Neural Networks",
                    "tgt_id": "Machine Learning",
                    "description": "Neural networks are a subset of machine learning",
                    "keywords": "subset, algorithm, learning",
                    "weight": 0.85,
                    "source_id": "chunk-123",
                    "file_path": "/documents/ai_basics.pdf",
                    "reference_id": "1"
                }
            ],
            "chunks": [
                {
                    "content": "Neural networks are computational models that mimic...",
                    "file_path": "/documents/ai_basics.pdf",
                    "chunk_id": "chunk-123",
                    "reference_id": "1"
                }
            ],
            "references": [
                {
                    "reference_id": "1",
                    "file_path": "/documents/ai_basics.pdf"
                }
            ]
        },
        "metadata": {
            "query_mode": "local",
            "keywords": {
                "high_level": ["neural", "networks"],
                "low_level": ["computation", "model"]
            },
            "processing_info": {
                "total_entities_found": 5,
                "total_relations_found": 3,
                "entities_after_truncation": 1,
                "relations_after_truncation": 1,
                "final_chunks_count": 1
            }
        }
    }


@pytest.fixture
def sample_paginated_documents_response():
    """Sample paginated documents response for testing."""
    return {
        "documents": [
            {
                "id": "doc_123",
                "content_summary": "Research paper on machine learning",
                "content_length": 15240,
                "status": "PROCESSED",
                "created_at": "2025-03-31T12:34:56",
                "updated_at": "2025-03-31T12:35:30",
                "track_id": "upload_20250729_170612_abc123",
                "chunks_count": 12,
                "error_msg": None,
                "metadata": {"author": "John Doe", "year": 2025},
                "file_path": "research_paper.pdf"
            }
        ],
        "pagination": {
            "page": 1,
            "page_size": 50,
            "total_count": 150,
            "total_pages": 3,
            "has_next": True,
            "has_prev": False
        },
        "status_counts": {
            "FAILED": 5,
            "PENDING": 10,
            "PREPROCESSED": 5,
            "PROCESSED": 130,
            "PROCESSING": 5
        }
    }


@pytest.fixture
def sample_graph_response():
    """Sample knowledge graph response for testing (API returns nodes/edges)."""
    return {
        "nodes": [
            {
                "id": "entity_123",
                "name": "Test Entity",
                "type": "concept",
                "properties": {"description": "A test entity"},
                "created_at": "2024-01-01T00:00:00Z"
            }
        ],
        "edges": [
            {
                "id": "rel_123",
                "source": "entity_123",
                "target": "entity_456",
                "type": "related_to",
                "properties": {"strength": "high"},
                "weight": 0.8
            }
        ],
        "total_entities": 1,
        "total_relations": 1
    }


@pytest.fixture
def sample_graph_labels_response():
    """Sample graph labels response for testing."""
    return {
        "entity_labels": ["Person", "Organization", "Location", "Concept"],
        "relation_labels": ["works_for", "located_in", "related_to", "part_of"]
    }


@pytest.fixture
def sample_popular_labels_response():
    """Sample popular labels response for testing."""
    return ["人工智能", "机器学习", "神经网络", "深度学习", "自然语言处理"]


@pytest.fixture
def sample_search_labels_response():
    """Sample search labels response for testing."""
    return ["人工智能", "AIGC", "AI应用"]


@pytest.fixture
def sample_health_response():
    """Sample health response for testing."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "uptime": 3600.0,
        "database_status": "connected",
        "cache_status": "active",
        "message": "All systems operational"
    }


@pytest.fixture
def sample_pipeline_status_response():
    """Sample pipeline status response for testing."""
    return {
        "status": "running",
        "progress": 75.5,
        "current_task": "processing documents",
        "message": "Pipeline is running normally"
    }


@pytest.fixture
def sample_status_counts_response():
    """Sample status counts response for testing."""
    return {
        "pending": 5,
        "processing": 2,
        "processed": 100,
        "failed": 1,
        "total": 108
    }