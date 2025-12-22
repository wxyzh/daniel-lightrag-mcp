# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Tool prefix support via `LIGHTRAG_TOOL_PREFIX` environment variable
  - Allows running multiple MCP server instances with different tool names
  - Automatically adds prefix to all tool names (e.g., `novel_style_query_text`)
  - Adds prefix marker to tool descriptions (e.g., `[novel_style] Query LightRAG with text`)
  - Essential for managing multiple LightRAG databases in the same MCP client

### Documentation
- Added `docs/MULTIPLE_INSTANCES_GUIDE.md` - Complete guide for running multiple instances
- Added `examples/multiple_instances.py` - Example configuration and usage patterns
- Added `examples/quick_start_multiple.py` - Interactive setup script
- Added `examples/test_prefix_demo.py` - Prefix functionality demonstration
- Added `.env.example` - Environment variable configuration template
- Updated `README.md` with multiple instances section
- Updated `CLAUDE.md` with prefix configuration details

### Tests
- Added `tests/test_tool_prefix.py` - Comprehensive tests for prefix functionality
  - Tests for `_add_tool_prefix()`, `_remove_tool_prefix()`, `_add_description_prefix()`
  - Round-trip tests to ensure prefix operations are reversible
  - Integration tests with `handle_list_tools()`

## [0.1.0] - 2024-12-21

### Added
- Initial release with 100% functional integration
- 22 fully working tools across 4 categories:
  - Document Management (6 tools)
  - Query Operations (2 tools)
  - Knowledge Graph (6 tools)
  - System Management (4 tools)
  - Health Check (1 tool)
- Comprehensive error handling with custom exception hierarchy
- Full LightRAG API 0.1.96+ support
- Async HTTP client with proper request/response handling
- Pydantic models for request/response validation
- Detailed logging with structured format
- Environment variable configuration support

### Fixed
- HTTP DELETE request handling with JSON bodies
- Request parameter validation aligned with LightRAG API
- Response model alignment with actual server responses
- File source implementation preventing database corruption
- Knowledge graph access with optimized label parameters

### Documentation
- Complete README with all tool descriptions
- Installation and configuration guides
- Usage examples and workflows
- Error handling documentation
- Troubleshooting guide
- Development setup instructions
