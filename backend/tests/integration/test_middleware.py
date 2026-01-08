import pytest
from httpx import AsyncClient
import time

@pytest.mark.asyncio
class TestAuthMiddleware:
    """認證中間件測試"""
    
    async def test_public_path_no_auth_required(self, client: AsyncClient):
        """測試公開路徑不需認證"""
        response = await client.get("/api/v1/health/")
        
        assert response.status_code == 200
    
    async def test_protected_path_requires_auth(self, client: AsyncClient):
        """測試受保護路徑需要認證"""
        response = await client.get("/api/v1/users/profile")
        
        assert response.status_code == 401
    
    async def test_response_contains_process_time_header(
        self, 
        client: AsyncClient
    ):
        """測試回應包含處理時間標頭"""
        response = await client.get("/api/v1/health/")
        
        assert "X-Process-Time" in response.headers
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0

@pytest.mark.asyncio
class TestRateLimitMiddleware:
    """速率限制中間件測試"""
    
    async def test_rate_limit_not_exceeded(self, client: AsyncClient):
        """測試未超過速率限制"""
        # 發送少量請求
        for _ in range(5):
            response = await client.get("/api/v1/health/")
            assert response.status_code == 200
    
    # 注意：完整的速率限制測試需要真實的 Redis 連接
    # 這裡的 fakeredis 可能無法完全模擬速率限制行為