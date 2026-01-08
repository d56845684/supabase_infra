import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestUserProfileAPI:
    """用戶資料 API 測試"""
    
    async def test_get_profile(self, authenticated_client):
        """測試取得用戶資料"""
        client, user_data = authenticated_client
        
        response = await client.get("/api/v1/users/profile")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
    
    async def test_get_profile_without_auth(self, client: AsyncClient):
        """測試未認證取得用戶資料"""
        response = await client.get("/api/v1/users/profile")
        
        assert response.status_code == 401

@pytest.mark.asyncio
class TestUserListAPI:
    """用戶列表 API 測試"""
    
    async def test_list_users_as_student(self, authenticated_client):
        """測試學生無權限列出用戶"""
        client, user_data = authenticated_client
        # 預設角色是 student
        
        response = await client.get("/api/v1/users/")
        
        # 學生應該無權限
        assert response.status_code == 403
    
    async def test_list_users_pagination(
        self, 
        authenticated_client, 
        mock_redis_service
    ):
        """測試用戶列表分頁"""
        client, user_data = authenticated_client
        
        # 修改用戶角色為 employee
        from app.core.security import create_token, TokenType
        token_data = {
            "sub": user_data["user_id"],
            "email": user_data["email"],
            "role": "employee",  # 改為員工
            "session_id": "test-session"
        }
        new_token = create_token(token_data, TokenType.ACCESS)
        client.cookies.set("access_token", new_token)
        
        response = await client.get("/api/v1/users/?page=1&per_page=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert "total" in data
        assert "page" in data
        assert data["page"] == 1
        assert data["per_page"] == 10
