import pytest
from httpx import AsyncClient
from unittest.mock import patch, Mock

@pytest.mark.asyncio
class TestAuthLoginAPI:
    """登入 API 測試"""
    
    async def test_login_success(self, client: AsyncClient, test_data):
        """測試成功登入"""
        login_data = test_data.create_login_request()
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "user" in data
        assert "tokens" in data
        assert data["user"]["email"] == login_data["email"]
        
        # 驗證 Cookies 已設定
        assert "access_token" in response.cookies
        assert "session_id" in response.cookies
    
    async def test_login_invalid_credentials(
        self, 
        client: AsyncClient, 
        mock_supabase_service
    ):
        """測試無效憑證登入"""
        # Mock 登入失敗
        mock_supabase_service.sign_in_with_password.side_effect = Exception(
            "Invalid login credentials"
        )
        
        response = await client.post("/api/v1/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
    
    async def test_login_missing_email(self, client: AsyncClient):
        """測試缺少 email"""
        response = await client.post("/api/v1/auth/login", json={
            "password": "testpassword"
        })
        
        assert response.status_code == 422  # Validation Error
    
    async def test_login_invalid_email_format(self, client: AsyncClient):
        """測試無效 email 格式"""
        response = await client.post("/api/v1/auth/login", json={
            "email": "not-an-email",
            "password": "testpassword"
        })
        
        assert response.status_code == 422

@pytest.mark.asyncio
class TestAuthLogoutAPI:
    """登出 API 測試"""
    
    async def test_logout_success(self, authenticated_client):
        """測試成功登出"""
        client, user_data = authenticated_client
        
        response = await client.post("/api/v1/auth/logout", json={})
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "登出成功"
    
    async def test_logout_all_devices(self, authenticated_client):
        """測試登出所有裝置"""
        client, user_data = authenticated_client
        
        response = await client.post("/api/v1/auth/logout", json={
            "logout_all_devices": True
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "所有裝置" in data["message"]
    
    async def test_logout_without_auth(self, client: AsyncClient):
        """測試未認證登出"""
        response = await client.post("/api/v1/auth/logout", json={})
        
        assert response.status_code == 401

@pytest.mark.asyncio
class TestAuthRefreshAPI:
    """Token 刷新 API 測試"""
    
    async def test_refresh_without_token(self, client: AsyncClient):
        """測試無 Refresh Token 刷新"""
        response = await client.post("/api/v1/auth/refresh")
        
        assert response.status_code == 401
    
    async def test_refresh_with_invalid_token(self, client: AsyncClient):
        """測試無效 Refresh Token"""
        client.cookies.set("refresh_token", "invalid-token")
        client.cookies.set("session_id", "invalid-session")
        
        response = await client.post("/api/v1/auth/refresh")
        
        assert response.status_code == 401

@pytest.mark.asyncio
class TestAuthMeAPI:
    """當前用戶 API 測試"""
    
    async def test_get_current_user(self, authenticated_client):
        """測試取得當前用戶資訊"""
        client, user_data = authenticated_client
        
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["id"] == user_data["user_id"]
        assert data["data"]["email"] == user_data["email"]
        assert data["data"]["role"] == user_data["role"]
    
    async def test_get_current_user_without_auth(self, client: AsyncClient):
        """測試未認證取得用戶資訊"""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401

@pytest.mark.asyncio
class TestAuthSessionsAPI:
    """Session 管理 API 測試"""
    
    async def test_get_user_sessions(self, authenticated_client):
        """測試取得用戶 Sessions"""
        client, user_data = authenticated_client
        
        response = await client.get("/api/v1/auth/sessions")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "sessions" in data
        assert data["total"] >= 1
        
        # 當前 Session 應該標記為 is_current
        current_sessions = [s for s in data["sessions"] if s["is_current"]]
        assert len(current_sessions) == 1
    
    async def test_get_sessions_without_auth(self, client: AsyncClient):
        """測試未認證取得 Sessions"""
        response = await client.get("/api/v1/auth/sessions")
        
        assert response.status_code == 401
