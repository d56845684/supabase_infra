import pytest
from httpx import AsyncClient
from app.core.security import create_token, TokenType

@pytest.mark.asyncio
class TestPermissionFlow:
    """權限流程端對端測試"""
    
    async def test_student_cannot_access_admin_resources(
        self,
        authenticated_client
    ):
        """測試學生無法存取管理員資源"""
        client, user_data = authenticated_client
        # user_data["role"] = "student"
        
        response = await client.get("/api/v1/users/")
        
        assert response.status_code == 403
    
    async def test_employee_can_access_user_list(
        self,
        client: AsyncClient,
        mock_redis_service
    ):
        """測試員工可以存取用戶列表"""
        from app.services.session_service import session_service
        session_service.redis = mock_redis_service
        
        # 建立員工 Session
        session_id, session_data = await session_service.create_session(
            user_id="employee-123",
            user_role="employee"
        )
        
        # 建立員工 Token
        token = create_token({
            "sub": "employee-123",
            "email": "employee@example.com",
            "role": "employee",
            "session_id": session_data.session_id
        }, TokenType.ACCESS)
        
        client.cookies.set("access_token", token)
        client.cookies.set("session_id", session_id)
        
        response = await client.get("/api/v1/users/")
        
        assert response.status_code == 200
    
    async def test_role_based_access_control(
        self,
        client: AsyncClient,
        mock_redis_service
    ):
        """測試角色存取控制"""
        from app.services.session_service import session_service
        session_service.redis = mock_redis_service
        
        roles_and_expected = [
            ("student", 403),   # 學生無權限
            ("teacher", 403),   # 教師無權限  
            ("employee", 200),  # 員工有權限
            ("admin", 200),     # 管理員有權限
        ]
        
        for role, expected_status in roles_and_expected:
            # 建立 Session
            session_id, session_data = await session_service.create_session(
                user_id=f"{role}-user",
                user_role=role
            )
            
            # 建立 Token
            token = create_token({
                "sub": f"{role}-user",
                "email": f"{role}@example.com",
                "role": role,
                "session_id": session_data.session_id
            }, TokenType.ACCESS)
            
            client.cookies.set("access_token", token)
            client.cookies.set("session_id", session_id)
            
            response = await client.get("/api/v1/users/")
            
            assert response.status_code == expected_status, \
                f"Role {role} expected {expected_status}, got {response.status_code}"

