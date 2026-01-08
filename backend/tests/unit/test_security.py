import pytest
from datetime import timedelta
from freezegun import freeze_time
from unittest.mock import Mock

from app.core.security import (
    create_token, decode_token, TokenType,
    generate_session_id, hash_session_id,
    set_auth_cookies, clear_auth_cookies,
    get_token_from_request
)

class TestTokenCreation:
    """Token 建立測試"""
    
    def test_create_access_token(self):
        """測試建立 Access Token"""
        data = {"sub": "user-123", "role": "student"}
        token = create_token(data, TokenType.ACCESS)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self):
        """測試建立 Refresh Token"""
        data = {"sub": "user-123"}
        token = create_token(data, TokenType.REFRESH)
        
        assert token is not None
        decoded = decode_token(token)
        assert decoded["type"] == TokenType.REFRESH
    
    def test_create_token_with_custom_expiry(self):
        """測試自訂過期時間"""
        data = {"sub": "user-123"}
        token = create_token(
            data, 
            TokenType.ACCESS,
            expires_delta=timedelta(hours=1)
        )
        
        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["sub"] == "user-123"
    
    def test_token_contains_required_claims(self):
        """測試 Token 包含必要的聲明"""
        data = {"sub": "user-123", "email": "test@example.com"}
        token = create_token(data, TokenType.ACCESS)
        
        decoded = decode_token(token)
        
        assert "sub" in decoded
        assert "exp" in decoded
        assert "iat" in decoded
        assert "type" in decoded
        assert decoded["email"] == "test@example.com"

class TestTokenDecoding:
    """Token 解碼測試"""
    
    def test_decode_valid_token(self):
        """測試解碼有效 Token"""
        data = {"sub": "user-123", "role": "admin"}
        token = create_token(data, TokenType.ACCESS)
        
        decoded = decode_token(token)
        
        assert decoded["sub"] == "user-123"
        assert decoded["role"] == "admin"
    
    def test_decode_invalid_token(self):
        """測試解碼無效 Token"""
        result = decode_token("invalid-token")
        assert result is None
    
    def test_decode_empty_token(self):
        """測試解碼空 Token"""
        result = decode_token("")
        assert result is None
    
    @freeze_time("2024-01-01 12:00:00")
    def test_decode_expired_token(self):
        """測試解碼過期 Token"""
        data = {"sub": "user-123"}
        token = create_token(
            data,
            TokenType.ACCESS,
            expires_delta=timedelta(seconds=-1)  # 已過期
        )
        
        result = decode_token(token)
        assert result is None

class TestSessionId:
    """Session ID 測試"""
    
    def test_generate_session_id_uniqueness(self):
        """測試 Session ID 唯一性"""
        ids = [generate_session_id() for _ in range(100)]
        assert len(ids) == len(set(ids))  # 全部唯一
    
    def test_generate_session_id_format(self):
        """測試 Session ID 格式"""
        session_id = generate_session_id()
        
        assert isinstance(session_id, str)
        assert len(session_id) >= 32
    
    def test_hash_session_id_consistency(self):
        """測試 Session ID 雜湊一致性"""
        session_id = "test-session-id"
        
        hash1 = hash_session_id(session_id)
        hash2 = hash_session_id(session_id)
        
        assert hash1 == hash2
    
    def test_hash_session_id_different_inputs(self):
        """測試不同輸入產生不同雜湊"""
        hash1 = hash_session_id("session-1")
        hash2 = hash_session_id("session-2")
        
        assert hash1 != hash2

class TestCookieOperations:
    """Cookie 操作測試"""
    
    def test_set_auth_cookies(self):
        """測試設定認證 Cookies"""
        response = Mock()
        response.set_cookie = Mock()
        
        set_auth_cookies(
            response,
            access_token="access-token",
            refresh_token="refresh-token",
            session_id="session-id"
        )
        
        # 驗證呼叫次數
        assert response.set_cookie.call_count == 3
        
        # 驗證 Cookie 名稱
        call_args = [call[1]["key"] for call in response.set_cookie.call_args_list]
        assert "access_token" in call_args
        assert "refresh_token" in call_args
        assert "session_id" in call_args
    
    def test_clear_auth_cookies(self):
        """測試清除認證 Cookies"""
        response = Mock()
        response.delete_cookie = Mock()
        
        clear_auth_cookies(response)
        
        assert response.delete_cookie.call_count == 3
    
    def test_get_token_from_cookie(self):
        """測試從 Cookie 取得 Token"""
        request = Mock()
        request.cookies = {"access_token": "my-token"}
        request.headers = {}
        
        token = get_token_from_request(request)
        assert token == "my-token"
    
    def test_get_token_from_header(self):
        """測試從 Header 取得 Token"""
        request = Mock()
        request.cookies = {}
        request.headers = {"Authorization": "Bearer my-bearer-token"}
        
        token = get_token_from_request(request)
        assert token == "my-bearer-token"
    
    def test_get_token_cookie_priority(self):
        """測試 Cookie 優先於 Header"""
        request = Mock()
        request.cookies = {"access_token": "cookie-token"}
        request.headers = {"Authorization": "Bearer header-token"}
        
        token = get_token_from_request(request)
        assert token == "cookie-token"
    
    def test_get_token_none_when_missing(self):
        """測試無 Token 時返回 None"""
        request = Mock()
        request.cookies = {}
        request.headers = {}
        
        token = get_token_from_request(request)
        assert token is None