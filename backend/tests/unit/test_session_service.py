import pytest
from datetime import datetime, timezone

from app.services.session_service import SessionService
from app.models.session import SessionData

@pytest.mark.asyncio
class TestSessionService:
    """Session 服務測試"""
    
    async def test_create_session(self, mock_session_service):
        """測試建立 Session"""
        session_id, session_data = await mock_session_service.create_session(
            user_id="user-123",
            user_role="student",
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1"
        )
        
        assert session_id is not None
        assert isinstance(session_data, SessionData)
        assert session_data.user_id == "user-123"
        assert session_data.user_role == "student"
    
    async def test_get_session(self, mock_session_service):
        """測試取得 Session"""
        # 建立 Session
        session_id, _ = await mock_session_service.create_session(
            user_id="user-123",
            user_role="teacher"
        )
        
        # 取得 Session
        session_data = await mock_session_service.get_session(session_id)
        
        assert session_data is not None
        assert session_data.user_id == "user-123"
        assert session_data.user_role == "teacher"
    
    async def test_get_nonexistent_session(self, mock_session_service):
        """測試取得不存在的 Session"""
        session_data = await mock_session_service.get_session("nonexistent-id")
        assert session_data is None
    
    async def test_update_session_activity(self, mock_session_service):
        """測試更新 Session 活動時間"""
        session_id, original = await mock_session_service.create_session(
            user_id="user-123",
            user_role="student"
        )
        
        # 更新活動時間
        result = await mock_session_service.update_session_activity(session_id)
        assert result is True
        
        # 驗證時間已更新
        updated = await mock_session_service.get_session(session_id)
        assert updated.last_activity >= original.last_activity
    
    async def test_destroy_session(self, mock_session_service):
        """測試銷毀 Session"""
        session_id, _ = await mock_session_service.create_session(
            user_id="user-123",
            user_role="student"
        )
        
        # 銷毀 Session
        result = await mock_session_service.destroy_session(session_id)
        assert result is True
        
        # 驗證已刪除
        session_data = await mock_session_service.get_session(session_id)
        assert session_data is None
    
    async def test_destroy_all_user_sessions(self, mock_session_service):
        """測試銷毀用戶所有 Sessions"""
        user_id = "user-456"
        
        # 建立多個 Sessions
        sessions = []
        for _ in range(3):
            sid, _ = await mock_session_service.create_session(
                user_id=user_id,
                user_role="student"
            )
            sessions.append(sid)
        
        # 銷毀所有 Sessions
        count = await mock_session_service.destroy_all_user_sessions(user_id)
        assert count == 3
        
        # 驗證全部已刪除
        for sid in sessions:
            data = await mock_session_service.get_session(sid)
            assert data is None
    
    async def test_get_user_sessions(self, mock_session_service):
        """測試取得用戶所有 Sessions"""
        user_id = "user-789"
        
        # 建立多個 Sessions
        for i in range(3):
            await mock_session_service.create_session(
                user_id=user_id,
                user_role="student",
                user_agent=f"Agent-{i}"
            )
        
        # 取得所有 Sessions
        sessions = await mock_session_service.get_user_sessions(user_id)
        
        assert len(sessions) == 3
        agents = [s.user_agent for s in sessions]
        assert "Agent-0" in agents
        assert "Agent-1" in agents
        assert "Agent-2" in agents
    
    async def test_blacklist_token(self, mock_session_service):
        """測試將 Token 加入黑名單"""
        token = "test-access-token"
        
        # 加入黑名單
        result = await mock_session_service.blacklist_token(token, 3600)
        assert result is True
        
        # 驗證在黑名單中
        is_blacklisted = await mock_session_service.is_token_blacklisted(token)
        assert is_blacklisted is True
    
    async def test_token_not_blacklisted(self, mock_session_service):
        """測試 Token 不在黑名單中"""
        is_blacklisted = await mock_session_service.is_token_blacklisted(
            "not-blacklisted-token"
        )
        assert is_blacklisted is False