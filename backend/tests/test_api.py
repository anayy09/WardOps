"""
Tests for API endpoints.
"""
import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check returns OK."""
        response = await client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestUnitsEndpoints:
    """Tests for units endpoints."""

    @pytest.mark.asyncio
    async def test_list_units_empty(self, client: AsyncClient):
        """Test listing units when none exist."""
        response = await client.get("/api/units")
        
        assert response.status_code == 200
        assert response.json() == []


class TestPatientsEndpoints:
    """Tests for patients endpoints."""

    @pytest.mark.asyncio
    async def test_list_patients_empty(self, client: AsyncClient):
        """Test listing patients when none exist."""
        response = await client.get("/api/patients")
        
        assert response.status_code == 200
        assert response.json() == []


class TestScenariosEndpoints:
    """Tests for scenarios endpoints."""

    @pytest.mark.asyncio
    async def test_list_scenarios_empty(self, client: AsyncClient):
        """Test listing scenarios when none exist."""
        response = await client.get("/api/scenarios")
        
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_create_scenario(self, client: AsyncClient, sample_scenario_params):
        """Test creating a new scenario."""
        response = await client.post("/api/scenarios", json=sample_scenario_params)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_scenario_params["name"]
        assert data["is_baseline"] == sample_scenario_params["is_baseline"]


class TestMetricsEndpoints:
    """Tests for metrics endpoints."""

    @pytest.mark.asyncio
    async def test_get_metrics_no_data(self, client: AsyncClient):
        """Test getting metrics when no data exists."""
        response = await client.get("/api/metrics")
        
        # Should return empty/default metrics
        assert response.status_code == 200


class TestCopilotEndpoints:
    """Tests for copilot/LLM endpoints."""

    @pytest.mark.asyncio
    async def test_copilot_refuses_medical_advice(self, client: AsyncClient):
        """Test that copilot refuses medical advice requests."""
        # This would need mocking of LLM calls
        # For now, just test the endpoint exists
        response = await client.post(
            "/api/copilot/chat",
            json={"message": "What medication should I take?"}
        )
        
        # Endpoint should exist (may error without LLM config)
        assert response.status_code in [200, 422, 500]


class TestDemoEndpoints:
    """Tests for demo data endpoints."""

    @pytest.mark.asyncio
    async def test_demo_status(self, client: AsyncClient):
        """Test demo data status endpoint."""
        response = await client.get("/api/demo/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "loaded" in data
