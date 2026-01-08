import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestCompleteAuthFlow:
    """完整認證流程端對端測試"""
    
    async def test_full_auth_lifecycle(
        self,
        client: AsyncClient,
        mock_supabase_service,
        mock_redis_service,
        test_data
    ):
        """測試完整認證生命週期：登入 -> 存取 -> 刷新 -> 登出"""
        
        # ========== Step 1: 登入 ==========
        login_data = test_data.create_login_request()
        login_response = await client.post(
            "/api/v1/auth/login", 
            json=login_data
        )
        
        assert login_response.status_code == 200
        login_result = login_response.json()
        assert login_result["success"] is True
        
        # 取得 Cookies
        access_token = login_response.cookies.get("access_token")
        session_id = login_response.cookies.get("session_id")
        
        assert access_token is not None
        assert session_id is not None
        
        # ========== Step 2: 存取受保護資源 ==========
        client.cookies.set("access_token", access_token)
        client.cookies.set("session_id", session_id)
        
        me_response = await client.get("/api/v1/auth/me")
        
        assert me_response.status_code == 200
        me_result = me_response.json()
        assert me_result["data"]["email"] == login_data["email"]
        
        # ========== Step 3: 查看 Sessions ==========
        sessions_response = await client.get("/api/v1/auth/sessions")
        
        assert sessions_response.status_code == 200
        sessions_result = sessions_response.json()
        assert sessions_result["total"] >= 1
        
        # ========== Step 4: 登出 ==========
        logout_response = await client.post(
            "/api/v1/auth/logout",
            json={"logout_all_devices": False}
        )
        
        assert logout_response.status_code == 200
        
        # ========== Step 5: 驗證登出後無法存取 ==========
        # 清除 cookies 模擬登出
        client.cookies.clear()
        
        protected_response = await client.get("/api/v1/auth/me")
        assert protected_response.status_code == 401
    
    async def test_multiple_device_login(
        self,
        client: AsyncClient,
        mock_supabase_service,
        mock_redis_service,
        test_data
    ):
        """測試多裝置登入"""
        login_data = test_data.create_login_request()
        
        # 裝置 1 登入
        response1 = await client.post("/api/v1/auth/login", json=login_data)
        assert response1.status_code == 200
        session1 = response1.cookies.get("session_id")
        
        # 裝置 2 登入 (模擬不同 User-Agent)
        headers = {"User-Agent": "Device-2-Browser"}
        response2 = await client.post(
            "/api/v1/auth/login", 
            json=login_data,
            headers=headers
        )
        assert response2.status_code == 200
        session2 = response2.cookies.get("session_id")
        
        # 兩個 Session 應該不同
        assert session1 != session2
    
    async def test_logout_all_devices_flow(
        self,
        client: AsyncClient,
        mock_supabase_service,
        mock_redis_service,
        test_data
    ):
        """測試登出所有裝置流程"""
        login_data = test_data.create_login_request()
        
        # 登入
        login_response = await client.post(
            "/api/v1/auth/login",
            json=login_data
        )
        
        client.cookies.set("access_token", login_response.cookies.get("access_token"))
        client.cookies.set("session_id", login_response.cookies.get("session_id"))
        
        # 登出所有裝置
        logout_response = await client.post(
            "/api/v1/auth/logout",
            json={"logout_all_devices": True}
        )
        
        assert logout_response.status_code == 200
        result = logout_response.json()
        assert "所有裝置" in result["message"]
