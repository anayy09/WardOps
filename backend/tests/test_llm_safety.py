"""
Tests for LLM safety and tool calling.
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.llm.tools import TOOL_DEFINITIONS
from app.llm.copilot import CopilotHandler


class TestLLMSafety:
    """Tests for LLM safety measures."""

    def test_tool_definitions_exist(self):
        """Test that all required tools are defined."""
        tool_names = [t["function"]["name"] for t in TOOL_DEFINITIONS]
        
        required_tools = [
            "query_bed_status",
            "get_staffing_info",
            "run_what_if",
            "find_policy",
            "forecast_demand",
        ]
        
        for tool in required_tools:
            assert tool in tool_names, f"Missing tool: {tool}"

    def test_tool_schemas_valid(self):
        """Test that tool schemas are valid JSON schema."""
        for tool in TOOL_DEFINITIONS:
            assert "type" in tool
            assert tool["type"] == "function"
            assert "function" in tool
            assert "name" in tool["function"]
            assert "description" in tool["function"]
            assert "parameters" in tool["function"]

    def test_medical_advice_refusal_patterns(self):
        """Test that medical advice refusal patterns exist."""
        medical_patterns = [
            "diagnosis",
            "treatment",
            "medication",
            "prescription",
            "medical advice",
            "should I take",
            "what drug",
        ]
        
        # These patterns should trigger refusal
        for pattern in medical_patterns:
            assert CopilotHandler._is_medical_request(pattern.lower())

    def test_operational_queries_allowed(self):
        """Test that operational queries are allowed."""
        operational_queries = [
            "What is the current bed occupancy?",
            "How many nurses are on shift?",
            "Show me the bottlenecks",
            "Run a simulation",
            "What is the imaging queue?",
        ]
        
        for query in operational_queries:
            assert not CopilotHandler._is_medical_request(query.lower())


class TestCopilotHandler:
    """Tests for copilot handler."""

    def test_handler_initialization(self):
        """Test handler initializes correctly."""
        handler = CopilotHandler()
        assert handler is not None

    @pytest.mark.asyncio
    async def test_medical_request_blocked(self):
        """Test that medical requests are blocked."""
        handler = CopilotHandler()
        
        with patch.object(handler, '_call_llm', new_callable=AsyncMock):
            response = await handler.process_message(
                "What medication should I prescribe?",
                db=None
            )
            
            assert "cannot provide medical advice" in response.lower() or \
                   "operational" in response.lower() or \
                   "sorry" in response.lower()

    def test_is_medical_request_detection(self):
        """Test medical request detection."""
        medical_queries = [
            "What diagnosis should I give?",
            "prescribe medication",
            "treatment plan",
            "should the patient take aspirin",
        ]
        
        for query in medical_queries:
            assert CopilotHandler._is_medical_request(query)
        
        ops_queries = [
            "bed occupancy",
            "staffing levels",
            "wait times",
            "simulation results",
        ]
        
        for query in ops_queries:
            assert not CopilotHandler._is_medical_request(query)


class TestToolExecution:
    """Tests for tool execution."""

    @pytest.mark.asyncio
    async def test_query_bed_status_tool(self):
        """Test query_bed_status tool execution."""
        from app.llm.tools import execute_tool
        
        with patch('app.llm.tools._get_db_session') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock the database query
            mock_session.execute.return_value.scalars.return_value.all.return_value = []
            
            result = await execute_tool(
                "query_bed_status",
                {"unit_id": 1},
                db=mock_session
            )
            
            assert result is not None

    @pytest.mark.asyncio
    async def test_unknown_tool_handling(self):
        """Test handling of unknown tool names."""
        from app.llm.tools import execute_tool
        
        result = await execute_tool(
            "unknown_tool",
            {},
            db=None
        )
        
        assert "error" in result.lower() or result is None


class TestCitations:
    """Tests for policy citation functionality."""

    @pytest.mark.asyncio
    async def test_policy_search_returns_citations(self):
        """Test that policy search returns proper citations."""
        from app.llm.tools import execute_tool
        
        with patch('app.llm.tools._search_policies') as mock_search:
            mock_search.return_value = [
                {
                    "title": "Nurse Ratio Guidelines",
                    "content": "The nurse to patient ratio...",
                    "source": "policy_doc_1",
                }
            ]
            
            result = await execute_tool(
                "find_policy",
                {"query": "nurse ratio"},
                db=None
            )
            
            # Result should include source information
            assert result is not None
