"""
Pydantic models for LightRAG API requests and responses.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


# Enums for status types and mode parameters
class DocStatus(str, Enum):
    """Document status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    PREPROCESSED = "preprocessed"
    PROCESSED = "processed"
    FAILED = "failed"


class QueryMode(str, Enum):
    """Query mode enumeration."""
    NAIVE = "naive"
    LOCAL = "local"
    GLOBAL = "global"
    HYBRID = "hybrid"
    MIX = "mix"
    BYPASS = "bypass"


class PipelineStatus(str, Enum):
    """Pipeline status enumeration."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# Common Models
class TextDocument(BaseModel):
    """Text document model."""
    title: Optional[str] = None
    content: str = Field(..., description="Document content")
    metadata: Optional[Dict[str, Any]] = None


class PaginationInfo(BaseModel):
    """Pagination information model."""
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(10, ge=1, le=100, description="Number of items per page")
    total_count: Optional[int] = Field(None, description="Total number of items")
    total_pages: Optional[int] = Field(None, description="Total number of pages")
    has_next: Optional[bool] = Field(None, description="Whether there is a next page")
    has_prev: Optional[bool] = Field(None, description="Whether there is a previous page")


class ValidationError(BaseModel):
    """Validation error model."""
    loc: List[Union[str, int]]
    msg: str
    type: str


class HTTPValidationError(BaseModel):
    """HTTP validation error model."""
    detail: List[ValidationError]


# Document Management Request Models
class InsertTextRequest(BaseModel):
    """Request model for inserting a single text document."""
    text: str = Field(..., description="Text content to insert")
    file_source: str = Field(default="text_input.txt", description="Source file name for the text")


class InsertTextsRequest(BaseModel):
    """Request model for inserting multiple text documents."""
    texts: List[str] = Field(..., description="List of text strings to insert")
    file_sources: List[str] = Field(default_factory=list, description="List of file sources for the texts")


class DeleteDocRequest(BaseModel):
    """Request model for deleting documents by IDs."""
    doc_ids: List[str] = Field(..., description="List of document IDs to delete")
    delete_file: bool = Field(default=False, description="Whether to delete the corresponding file in the upload directory")
    delete_llm_cache: bool = Field(default=False, description="Whether to delete cached LLM extraction results for the documents")


class DeleteEntityRequest(BaseModel):
    """Request model for deleting an entity."""
    entity_name: str = Field(..., description="Name of the entity to delete")


class DeleteRelationRequest(BaseModel):
    """Request model for deleting a relation."""
    source_entity: str = Field(..., description="Source entity name")
    target_entity: str = Field(..., description="Target entity name")


class DocumentsRequest(BaseModel):
    """Request model for paginated documents."""
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(10, ge=1, le=100, description="Number of items per page")
    status_filter: Optional[DocStatus] = None


class ClearCacheRequest(BaseModel):
    """Request model for clearing cache."""
    cache_type: Optional[str] = None


# Query Request Models
class QueryRequest(BaseModel):
    """Request model for text queries."""
    query: str = Field(..., min_length=3, description="Query text")
    mode: QueryMode = Field(QueryMode.MIX, description="Query mode")
    only_need_context: bool = Field(False, description="Whether to only return context without generation")
    only_need_prompt: bool = Field(False, description="Whether to only return the prompt")
    stream: bool = Field(True, description="Whether to stream results")

    # Advanced retrieval parameters
    top_k: Optional[int] = Field(None, ge=1, description="Number of top results to retrieve")
    chunk_top_k: Optional[int] = Field(None, ge=1, description="Number of text chunks to retrieve")
    max_entity_tokens: Optional[int] = Field(None, ge=1, description="Maximum entity tokens for local mode")
    max_relation_tokens: Optional[int] = Field(None, ge=1, description="Maximum relation tokens for global mode")
    max_total_tokens: Optional[int] = Field(None, ge=1, description="Maximum total tokens budget")

    # Reference and reranking parameters
    include_references: bool = Field(True, description="Whether to include references in response")
    include_chunk_content: bool = Field(False, description="Whether to include chunk content in references")
    enable_rerank: bool = Field(True, description="Whether to enable reranking")

    # Keywords parameters - use default_factory=list to avoid None serialization
    hl_keywords: List[str] = Field(default_factory=list, description="High-level keywords for retrieval")
    ll_keywords: List[str] = Field(default_factory=list, description="Low-level keywords for retrieval")

    # Conversation history
    conversation_history: Optional[List[Dict[str, str]]] = Field(None, description="Conversation history for multi-turn queries")

    # Response control
    response_type: Optional[str] = Field(None, description="Response format (e.g., 'Multiple Paragraphs', 'Single Paragraph')")
    user_prompt: Optional[str] = Field(None, description="User-provided prompt for the query")


# Knowledge Graph Request Models
class EntityUpdateRequest(BaseModel):
    """Request model for updating an entity."""
    entity_name: str = Field(..., description="Name of the entity to update")
    updated_data: Dict[str, Any] = Field(..., description="Updated data for the entity")
    allow_rename: bool = Field(False, description="Whether to allow entity renaming")
    allow_merge: bool = Field(False, description="Whether to merge into existing entity when renaming")


class RelationUpdateRequest(BaseModel):
    """Request model for updating a relation."""
    # relation_id: str = Field(..., description="ID of the relation to update")
    source_id: str = Field(..., description="Source entity ID")
    target_id: str = Field(..., description="Target entity ID")
    updated_data: Dict[str, Any] = Field(..., description="Updated data for the relation")


class EntityExistsRequest(BaseModel):
    """Request model for checking if entity exists."""
    entity_name: str = Field(..., description="Name of the entity to check")


class CreateEntityRequest(BaseModel):
    """Request model for creating a new entity."""
    entity_name: str = Field(..., description="Name of the new entity")
    entity_data: Dict[str, Any] = Field(..., description="Entity properties (e.g., description, entity_type)")


class CreateRelationRequest(BaseModel):
    """Request model for creating a new relation."""
    source_entity: str = Field(..., description="Source entity name")
    target_entity: str = Field(..., description="Target entity name")
    relation_data: Dict[str, Any] = Field(..., description="Relation properties (e.g., description, keywords, weight)")


# Authentication Request Models
class LoginRequest(BaseModel):
    """Request model for login."""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


# Document Management Response Models
class InsertResponse(BaseModel):
    """Response model for document insertion."""
    status: str = Field(..., description="Insertion status")
    message: str = Field(..., description="Status message")
    track_id: Optional[str] = Field(None, description="Tracking ID for the insertion")
    id: Optional[str] = None


class ScanResponse(BaseModel):
    """Response model for document scanning."""
    status: str = Field(..., description="Scanning status")
    message: Optional[str] = Field(None, description="Status message")
    track_id: str = Field(..., description="Tracking ID for the scan operation")
    new_documents: List[str] = Field(default_factory=list, description="List of new document names")


class UploadResponse(BaseModel):
    """Response model for file upload."""
    status: str = Field(..., description="Upload status")
    message: Optional[str] = None
    track_id: Optional[str] = Field(None, description="Track ID for upload")


class DocumentInfo(BaseModel):
    """Document information model."""
    id: str = Field(..., description="Document ID")
    content_length: Optional[int] = Field(None, description="Length of document content in characters")
    status: DocStatus = Field(..., description="Document status")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    track_id: Optional[str] = Field(None, description="Tracking ID for monitoring progress")
    chunks_count: Optional[int] = Field(None, description="Number of chunks the document was split into")
    error_msg: Optional[str] = Field(None, description="Error message if processing failed")
    metadata: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = Field(None, description="Original file path")


class DocumentsResponse(BaseModel):
    """Response model for retrieving documents."""
    statuses: Dict[str, Any] = Field(default_factory=dict, description="Document statuses")


class PaginatedDocsResponse(BaseModel):
    """Response model for paginated documents."""
    documents: List[DocumentInfo] = Field(default_factory=list)
    pagination: PaginationInfo = Field(..., description="Pagination information")
    status_counts: Dict[str, int] = Field(default_factory=dict, description="Status counts")


class DeleteDocByIdResponse(BaseModel):
    """Response model for document deletion by ID."""
    status: str = Field(..., description="Deletion status")
    message: Optional[str] = None
    doc_id: Optional[str] = Field(None, description="ID of the deleted document")


class ClearDocumentsResponse(BaseModel):
    """Response model for clearing all documents."""
    status: str = Field(..., description="Clearing status")
    message: Optional[str] = None


class PipelineStatusResponse(BaseModel):
    """Response model for pipeline status."""
    autoscanned: bool = Field(..., description="Whether auto-scanning is enabled")
    busy: bool = Field(..., description="Whether pipeline is busy")
    job_name: Optional[str] = None
    job_start: Optional[str] = None
    docs: Optional[int] = None
    batchs: Optional[int] = None
    cur_batch: Optional[int] = None
    request_pending: Optional[bool] = None
    latest_message: Optional[str] = None
    history_messages: Optional[List[str]] = None
    update_status: Optional[Dict[str, Any]] = None
    progress: Optional[float] = Field(None, ge=0, le=100, description="Progress percentage")
    current_task: Optional[str] = None
    message: Optional[str] = None


class TrackStatusResponse(BaseModel):
    """Response model for track status."""
    track_id: str = Field(..., description="Track ID")
    documents: List[Dict[str, Any]] = Field(default_factory=list, description="Documents in track")
    total_count: int = Field(0, description="Total document count")
    status_summary: Dict[str, Any] = Field(default_factory=dict, description="Status summary")


class StatusCountsResponse(BaseModel):
    """Response model for document status counts."""
    status_counts: Dict[str, int] = Field(..., description="Status counts mapping")


class ClearCacheResponse(BaseModel):
    """Response model for cache clearing."""
    status: str = Field(..., description="Cache clearing status")
    message: Optional[str] = Field(None, description="Status message")
    cache_type: Optional[str] = None


class DeletionResult(BaseModel):
    """Response model for entity/relation deletion."""
    status: str = Field(..., description="Deletion status (success/not_found/fail)")
    doc_id: str = Field(..., description="Document/entity ID")
    message: str = Field(..., description="Status message")
    status_code: int = Field(default=200, description="Status code")
    file_path: Optional[str] = Field(None, description="File path if applicable")


# Query Response Models
class QueryResult(BaseModel):
    """Query result model for displaying retrieved content."""
    document_id: str = Field(..., description="Document ID")
    snippet: str = Field(..., description="Text snippet from the document")
    score: Optional[float] = Field(None, ge=0, le=1, description="Relevance score")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ReferenceItem(BaseModel):
    """Reference item for query responses."""
    reference_id: str = Field(..., description="Unique reference identifier")
    file_path: str = Field(..., description="Path to the source file")
    content: Optional[List[str]] = Field(None, description="List of chunk contents (only when include_chunk_content=True)")


class QueryResponse(BaseModel):
    """Response model for text queries."""
    response: Optional[str] = Field(None, description="Query response text generated by LLM")
    results: Optional[List[QueryResult]] = Field(None, description="Retrieved content for display")
    references: Optional[List[ReferenceItem]] = Field(None, description="Reference list for citation (only when include_references=True)")


# Query Data Models (for /query/data endpoint)
class QueryDataEntity(BaseModel):
    """Entity retrieved from knowledge graph."""
    entity_name: str = Field(..., description="Name of the entity")
    entity_type: Optional[str] = Field(None, description="Type/category of the entity")
    description: Optional[str] = Field(None, description="Entity description")
    source_id: Optional[str] = Field(None, description="Source chunk ID")
    file_path: Optional[str] = Field(None, description="Path to the source file")
    reference_id: Optional[str] = Field(None, description="Reference identifier")


class QueryDataRelation(BaseModel):
    """Relationship retrieved from knowledge graph."""
    src_id: str = Field(..., description="Source entity name")
    tgt_id: str = Field(..., description="Target entity name")
    description: Optional[str] = Field(None, description="Relationship description")
    keywords: Optional[str] = Field(None, description="Comma-separated keywords")
    weight: Optional[float] = Field(None, ge=0, description="Relationship weight (can exceed 1.0)")
    source_id: Optional[str] = Field(None, description="Source chunk ID")
    file_path: Optional[str] = Field(None, description="Path to the source file")
    reference_id: Optional[str] = Field(None, description="Reference identifier")


class QueryDataChunk(BaseModel):
    """Text chunk retrieved from vector database."""
    content: str = Field(..., description="Chunk text content")
    file_path: Optional[str] = Field(None, description="Path to the source file")
    chunk_id: Optional[str] = Field(None, description="Chunk identifier")
    reference_id: Optional[str] = Field(None, description="Reference identifier")


class QueryData(BaseModel):
    """Structured data retrieved by query_data endpoint."""
    entities: List[QueryDataEntity] = Field(default_factory=list, description="Retrieved entities")
    relationships: List[QueryDataRelation] = Field(default_factory=list, description="Retrieved relationships")
    chunks: List[QueryDataChunk] = Field(default_factory=list, description="Retrieved text chunks")
    references: List[ReferenceItem] = Field(default_factory=list, description="Reference list")


class QueryDataMetadata(BaseModel):
    """Metadata for query_data response."""
    query_mode: str = Field(..., description="Query mode used")
    keywords: Dict[str, List[str]] = Field(default_factory=dict, description="High-level and low-level keywords")
    processing_info: Dict[str, int] = Field(default_factory=dict, description="Processing statistics")


class QueryDataResponse(BaseModel):
    """Response model for query_data endpoint."""
    status: str = Field(..., description="Query execution status (success/failure)")
    message: str = Field(..., description="Status message")
    data: QueryData = Field(..., description="Retrieved structured data")
    metadata: QueryDataMetadata = Field(..., description="Query metadata")


# Knowledge Graph Response Models
class EntityInfo(BaseModel):
    """Entity information model."""
    id: str = Field(..., description="Entity ID")
    name: str = Field(..., description="Entity name")
    type: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RelationInfo(BaseModel):
    """Relation information model."""
    id: str = Field(..., description="Relation ID")
    source_entity: str = Field(..., description="Source entity ID")
    target_entity: str = Field(..., description="Target entity ID")
    type: str = Field(..., description="Relation type")
    properties: Dict[str, Any] = Field(default_factory=dict)
    weight: Optional[float] = Field(None, ge=0, description="Relation weight (can exceed 1.0)")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class GraphResponse(BaseModel):
    """Response model for knowledge graph."""
    nodes: List[Dict[str, Any]] = Field(default_factory=list, description="Graph nodes (entities)")
    edges: List[Dict[str, Any]] = Field(default_factory=list, description="Graph edges (relations)")
    is_truncated: bool = Field(False, description="Whether the graph is truncated")
    
    @property
    def entities(self) -> List[Dict[str, Any]]:
        """Alias for nodes to maintain backward compatibility."""
        return self.nodes
    
    @property
    def relations(self) -> List[Dict[str, Any]]:
        """Alias for edges to maintain backward compatibility."""
        return self.edges


class LabelsResponse(BaseModel):
    """Response model for graph labels."""
    entity_labels: List[str] = Field(default_factory=list)
    relation_labels: List[str] = Field(default_factory=list)


class EntityExistsResponse(BaseModel):
    """Response model for entity existence check."""
    exists: bool = Field(..., description="Whether entity exists")
    entity_name: Optional[str] = None
    entity_id: Optional[str] = None


class EntityUpdateResponse(BaseModel):
    """Response model for entity update."""
    status: str = Field(..., description="Update status")
    message: str = Field(..., description="Update message")
    data: Dict[str, Any] = Field(..., description="Updated entity data")


class RelationUpdateResponse(BaseModel):
    """Response model for relation update."""
    status: str = Field(..., description="Update status")
    message: str = Field(..., description="Update message")
    data: Dict[str, Any] = Field(..., description="Updated relation data")


# System Management Response Models
class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Health status")
    version: Optional[str] = None
    uptime: Optional[float] = None
    database_status: Optional[str] = None
    cache_status: Optional[str] = None
    message: Optional[str] = None


# Authentication Response Models
class AuthStatusResponse(BaseModel):
    """Response model for authentication status."""
    authenticated: bool = Field(..., description="Whether user is authenticated")
    user: Optional[str] = None


class LoginResponse(BaseModel):
    """Response model for login."""
    success: bool = Field(..., description="Whether login was successful")
    token: Optional[str] = None
    user: Optional[str] = None
    message: Optional[str] = None


# Ollama API Models (for completeness)
class OllamaVersionResponse(BaseModel):
    """Response model for Ollama version."""
    version: str = Field(..., description="Ollama version")


class OllamaTagsResponse(BaseModel):
    """Response model for Ollama tags."""
    models: List[Dict[str, Any]] = Field(default_factory=list)


class OllamaProcessResponse(BaseModel):
    """Response model for Ollama running processes."""
    models: List[Dict[str, Any]] = Field(default_factory=list)


class OllamaGenerateRequest(BaseModel):
    """Request model for Ollama generate."""
    model: str = Field(..., description="Model name")
    prompt: str = Field(..., description="Prompt text")
    stream: bool = Field(False, description="Whether to stream response")


class OllamaChatMessage(BaseModel):
    """Chat message model for Ollama."""
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")


class OllamaChatRequest(BaseModel):
    """Request model for Ollama chat."""
    model: str = Field(..., description="Model name")
    messages: List[OllamaChatMessage] = Field(..., description="Chat messages")
    stream: bool = Field(False, description="Whether to stream response")


# File upload models
class Body_upload_to_input_dir_documents_upload_post(BaseModel):
    """Request body for file upload."""
    file: bytes = Field(..., description="File content")


class Body_login_login_post(BaseModel):
    """Request body for login."""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


# Status response models
class DocStatusResponse(BaseModel):
    """Response model for document status."""
    document_id: str = Field(..., description="Document ID")
    status: DocStatus = Field(..., description="Document status")
    message: Optional[str] = None


class DocsStatusesResponse(BaseModel):
    """Response model for multiple document statuses."""
    statuses: List[DocStatusResponse] = Field(default_factory=list)
    total: int = Field(0, ge=0)


# Additional missing models for API alignment
class ReprocessResponse(BaseModel):
    """Response model for reprocessing failed documents."""
    status: str = Field(default="reprocessing_started", description="Status of the reprocessing operation")
    message: str = Field(..., description="Human-readable message describing the operation")
    track_id: str = Field(..., description="Tracking ID for monitoring reprocessing progress")


class CancelPipelineResponse(BaseModel):
    """Response model for pipeline cancellation."""
    status: str = Field(..., description="Status of the cancellation request (cancellation_requested/not_busy)")
    message: str = Field(..., description="Human-readable message describing the operation")


class EntityMergeRequest(BaseModel):
    """Request model for merging entities."""
    entities_to_change: List[str] = Field(..., description="List of entity names to be merged and deleted")
    entity_to_change_into: str = Field(..., description="Target entity name that will receive all relationships")


class ClearDocumentsResponse(BaseModel):
    """Response model for clearing all documents."""
    status: str = Field(..., description="Clearing status (success/partial_success/busy/fail)")
    message: str = Field(..., description="Message describing the operation result")


class SearchLabelsResponse(BaseModel):
    """Response model for searching graph labels."""
    labels: List[str] = Field(default_factory=list, description="List of matching labels sorted by relevance")


class PopularLabelsResponse(BaseModel):
    """Response model for getting popular labels."""
    labels: List[str] = Field(default_factory=list, description="List of popular labels sorted by degree")