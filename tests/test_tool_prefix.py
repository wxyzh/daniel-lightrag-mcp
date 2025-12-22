"""
Tests for tool prefix functionality.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from mcp.types import Tool

# Import functions we need to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from daniel_lightrag_mcp.server import (
    _add_tool_prefix,
    _remove_tool_prefix,
    _add_description_prefix,
    handle_list_tools,
)


class TestToolPrefixFunctions:
    """Test the prefix helper functions."""

    def test_add_tool_prefix_with_prefix(self):
        """Test adding prefix to tool name when prefix is set."""
        with patch('daniel_lightrag_mcp.server.TOOL_PREFIX', 'test_'):
            assert _add_tool_prefix('query_text') == 'test_query_text'
            assert _add_tool_prefix('insert_text') == 'test_insert_text'

    def test_add_tool_prefix_without_prefix(self):
        """Test adding prefix when no prefix is set."""
        with patch('daniel_lightrag_mcp.server.TOOL_PREFIX', ''):
            assert _add_tool_prefix('query_text') == 'query_text'
            assert _add_tool_prefix('insert_text') == 'insert_text'

    def test_remove_tool_prefix_with_prefix(self):
        """Test removing prefix from tool name when prefix is set."""
        with patch('daniel_lightrag_mcp.server.TOOL_PREFIX', 'test_'):
            assert _remove_tool_prefix('test_query_text') == 'query_text'
            assert _remove_tool_prefix('test_insert_text') == 'insert_text'

    def test_remove_tool_prefix_without_prefix(self):
        """Test removing prefix when no prefix is set."""
        with patch('daniel_lightrag_mcp.server.TOOL_PREFIX', ''):
            assert _remove_tool_prefix('query_text') == 'query_text'
            assert _remove_tool_prefix('insert_text') == 'insert_text'

    def test_remove_tool_prefix_non_matching(self):
        """Test removing prefix when name doesn't start with prefix."""
        with patch('daniel_lightrag_mcp.server.TOOL_PREFIX', 'test_'):
            # Should return original name if it doesn't start with prefix
            assert _remove_tool_prefix('query_text') == 'query_text'
            assert _remove_tool_prefix('other_query_text') == 'other_query_text'

    def test_add_description_prefix_with_prefix(self):
        """Test adding prefix to description when prefix is set."""
        with patch('daniel_lightrag_mcp.server.TOOL_PREFIX', 'test_'):
            result = _add_description_prefix('Query LightRAG with text')
            assert result == '[test] Query LightRAG with text'

    def test_add_description_prefix_with_underscore_prefix(self):
        """Test adding prefix to description with trailing underscore."""
        with patch('daniel_lightrag_mcp.server.TOOL_PREFIX', 'novel_style_'):
            result = _add_description_prefix('Query LightRAG with text')
            assert result == '[novel_style] Query LightRAG with text'

    def test_add_description_prefix_without_prefix(self):
        """Test adding prefix when no prefix is set."""
        with patch('daniel_lightrag_mcp.server.TOOL_PREFIX', ''):
            result = _add_description_prefix('Query LightRAG with text')
            assert result == 'Query LightRAG with text'


class TestToolListWithPrefix:
    """Test the tool list generation with prefixes."""

    @pytest.mark.asyncio
    async def test_list_tools_with_prefix(self):
        """Test that tools are listed with prefix when TOOL_PREFIX is set."""
        with patch('daniel_lightrag_mcp.server.TOOL_PREFIX', 'novel_'):
            tools = await handle_list_tools()

            # Check that we have all 22 tools
            assert len(tools) >= 20  # At least 20 tools expected

            # Check that all tools have the prefix
            for tool in tools:
                assert isinstance(tool, Tool)
                assert tool.name.startswith('novel_')
                assert '[novel]' in tool.description or tool.description.startswith('[novel]')

    @pytest.mark.asyncio
    async def test_list_tools_without_prefix(self):
        """Test that tools are listed without prefix when TOOL_PREFIX is not set."""
        with patch('daniel_lightrag_mcp.server.TOOL_PREFIX', ''):
            tools = await handle_list_tools()

            # Check that we have all 22 tools
            assert len(tools) >= 20

            # Check specific tools
            tool_names = [tool.name for tool in tools]
            assert 'query_text' in tool_names
            assert 'insert_text' in tool_names
            assert 'get_health' in tool_names

            # Check that descriptions don't have prefix markers
            for tool in tools:
                assert not tool.description.startswith('[')

    @pytest.mark.asyncio
    async def test_tool_names_consistency(self):
        """Test that all tool names are prefixed consistently."""
        with patch('daniel_lightrag_mcp.server.TOOL_PREFIX', 'test_prefix_'):
            tools = await handle_list_tools()

            # All tools should have the same prefix
            for tool in tools:
                assert tool.name.startswith('test_prefix_')

                # Extract original name
                original_name = tool.name[len('test_prefix_'):]

                # Original name should not be empty
                assert len(original_name) > 0

                # Description should have prefix marker
                assert tool.description.startswith('[test_prefix]')


class TestRoundTripPrefixing:
    """Test that prefix add/remove operations are reversible."""

    def test_roundtrip_with_prefix(self):
        """Test that add+remove returns original name."""
        with patch('daniel_lightrag_mcp.server.TOOL_PREFIX', 'test_'):
            original = 'query_text'
            prefixed = _add_tool_prefix(original)
            unprefixed = _remove_tool_prefix(prefixed)
            assert unprefixed == original

    def test_roundtrip_without_prefix(self):
        """Test roundtrip when no prefix is set."""
        with patch('daniel_lightrag_mcp.server.TOOL_PREFIX', ''):
            original = 'query_text'
            prefixed = _add_tool_prefix(original)
            unprefixed = _remove_tool_prefix(prefixed)
            assert unprefixed == original

    def test_roundtrip_multiple_tools(self):
        """Test roundtrip with multiple tool names."""
        tool_names = [
            'query_text',
            'insert_text',
            'get_health',
            'get_knowledge_graph',
            'delete_document',
        ]

        with patch('daniel_lightrag_mcp.server.TOOL_PREFIX', 'prefix_'):
            for name in tool_names:
                prefixed = _add_tool_prefix(name)
                unprefixed = _remove_tool_prefix(prefixed)
                assert unprefixed == name, f"Roundtrip failed for {name}"


class TestEnvironmentVariableIntegration:
    """Test reading prefix from environment variable."""

    def test_prefix_from_env_var(self):
        """Test that prefix is read from LIGHTRAG_TOOL_PREFIX env var."""
        # This test verifies the integration at module load time
        # Note: Since TOOL_PREFIX is read at module import, we can only test
        # the current state. Full env var testing would require subprocess.

        # Just verify the TOOL_PREFIX variable exists and is a string
        from daniel_lightrag_mcp.server import TOOL_PREFIX
        assert isinstance(TOOL_PREFIX, str)

    @patch.dict(os.environ, {'LIGHTRAG_TOOL_PREFIX': 'env_test_'})
    def test_prefix_usage_pattern(self):
        """Test the expected usage pattern with env var."""
        # Simulate what happens when the module is loaded with env var
        prefix = os.getenv('LIGHTRAG_TOOL_PREFIX', '')
        assert prefix == 'env_test_'

        # Test the functions would work correctly
        with patch('daniel_lightrag_mcp.server.TOOL_PREFIX', prefix):
            assert _add_tool_prefix('query_text') == 'env_test_query_text'
            assert _remove_tool_prefix('env_test_query_text') == 'query_text'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
