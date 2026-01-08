import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestHealthAPI:
    """健康檢查 API 測試"""
    
    async def test_health_check(self, client: AsyncClient):
        """測試基本健康檢查"""
        response = await client.get("/api/v1/health/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    async def test_readiness_check(self, client: AsyncClient):
        """測試就緒檢查"""
        response = await client.get("/api/v1/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "checks" in data
        assert "redis" in data["checks"]
        assert "supabase" in data["checks"]

