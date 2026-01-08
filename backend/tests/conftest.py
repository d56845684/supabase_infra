import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

import fakeredis.aioredis
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from app.main import app
from app.config import Settings, get_settings
from app.services.redis_service import RedisService, redis_service
from app.services.session_service import SessionService, session_service
from app.services.supabase_service import SupabaseService
from app.core.security import create_token, TokenType

# ============================================
# 測試設定
# ============================================

def get_test_settings() -> Settings:
    """測試環境設定"""
    return Settings(
        APP_NAME="Test App",
        APP_ENV="test",
        DEBUG=True,
        SECRET_KEY="test-secret-key-for-testing-only",
        SUPABASE_URL="https://test.supabase.co",
        SUPABASE_ANON_KEY="test-anon-key",
        SUPABASE_SERVICE_ROLE_KEY="test-service-role-key",
        SUPABASE_JWT_SECRET="test-jwt-secret",
        REDIS_URL="redis://localhost:6379/0",
        COOKIE_DOMAIN="localhost",
        COOKIE_SECURE=False,
        SESSION_EXPIRE_MINUTES=60,
        ACCESS_TOKEN_EXPIRE_MINUTES=15,
        REFRESH_TOKEN_EXPIRE_DAYS=7
    )

# ============================================
# Pytest 配置
# ============================================

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """建立事件循環"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_settings() -> Settings:
    """測試設定 fixture"""
    return get_test_settings()

# ============================================
# Fake Redis Fixture
# ============================================

@pytest.fixture
async def fake_redis() -> AsyncGenerator:
    """Fake Redis 用於測試"""
    server = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield server
    await server.flushall()
    await server.close()

@pytest.fixture
async def mock_redis_service(fake_redis) -> AsyncGenerator:
    """Mock Redis Service"""
    service = RedisService()
    service._client = fake_redis
    service._pool = Mock()
    
    # 替換全域 redis_service
    original_client = redis_service._client
    redis_service._client = fake_redis
    
    yield service
    
    redis_service._client = original_client

@pytest.fixture
async def mock_session_service(mock_redis_service) -> SessionService:
    """Mock Session Service"""
    service = SessionService()
    service.redis = mock_redis_service
    return service

# ============================================
# Mock Supabase Fixture
# ============================================

@pytest.fixture
def mock_supabase_user():
    """模擬 Supabase 用戶"""
    return Mock(
        id="test-user-id-123",
        email="test@example.com",
        email_confirmed_at=datetime.now(timezone.utc).isoformat(),
        created_at=datetime.now(timezone.utc).isoformat(),
        user_metadata={"name": "Test User", "role": "student"}
    )

@pytest.fixture
def mock_supabase_session(mock_supabase_user):
    """模擬 Supabase Session"""
    return Mock(
        access_token="supabase-access-token",
        refresh_token="supabase-refresh-token",
        user=mock_supabase_user
    )

@pytest.fixture
def mock_supabase_service(mock_supabase_user, mock_supabase_session):
    """Mock Supabase Service"""
    service = Mock(spec=SupabaseService)
    
    # Mock sign_in_with_password
    auth_response = Mock()
    auth_response.user = mock_supabase_user
    auth_response.session = mock_supabase_session
    service.sign_in_with_password.return_value = auth_response
    
    # Mock sign_up
    signup_response = Mock()
    signup_response.user = mock_supabase_user
    service.sign_up.return_value = signup_response
    
    # Mock sign_out
    service.sign_out.return_value = None
    
    # Mock admin table query
    table_mock = Mock()
    table_mock.select.return_value = table_mock
    table_mock.eq.return_value = table_mock
    table_mock.single.return_value = table_mock
    table_mock.execute.return_value = Mock(data={"role": "student"})
    
    service.admin = Mock()
    service.admin.table.return_value = table_mock
    
    return service

# ============================================
# Test Client Fixture
# ============================================

@pytest.fixture
async def client(
    mock_redis_service,
    mock_supabase_service,
    test_settings
) -> AsyncGenerator[AsyncClient, None]:
    """建立測試客戶端"""
    # Override dependencies
    app.dependency_overrides[get_settings] = lambda: test_settings
    
    # Patch services
    with patch('app.services.auth_service.supabase_service', mock_supabase_service), \
         patch('app.services.auth_service.redis_service', mock_redis_service), \
         patch('app.api.v1.auth.supabase_service', mock_supabase_service):
        
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test"
        ) as ac:
            yield ac
    
    app.dependency_overrides.clear()

@pytest.fixture
async def authenticated_client(
    client: AsyncClient,
    mock_redis_service,
    test_settings
) -> AsyncGenerator[tuple[AsyncClient, dict], None]:
    """已認證的測試客戶端"""
    # 建立測試用戶資訊
    user_data = {
        "user_id": "test-user-id-123",
        "email": "test@example.com",
        "role": "student"
    }
    
    # 建立 Session
    from app.services.session_service import session_service
    session_service.redis = mock_redis_service
    
    session_id, session_data = await session_service.create_session(
        user_id=user_data["user_id"],
        user_role=user_data["role"],
        user_agent="pytest",
        ip_address="127.0.0.1"
    )
    
    # 建立 Token
    token_data = {
        "sub": user_data["user_id"],
        "email": user_data["email"],
        "role": user_data["role"],
        "session_id": session_data.session_id
    }
    access_token = create_token(token_data, TokenType.ACCESS)
    
    # 設定 Cookies
    client.cookies.set("access_token", access_token)
    client.cookies.set("session_id", session_id)
    
    yield client, user_data

# ============================================
# 測試資料工廠
# ============================================

class TestDataFactory:
    """測試資料工廠"""
    
    @staticmethod
    def create_user(
        user_id: str = "test-user-123",
        email: str = "test@example.com",
        role: str = "student"
    ) -> dict:
        return {
            "user_id": user_id,
            "email": email,
            "role": role
        }
    
    @staticmethod
    def create_login_request(
        email: str = "test@example.com",
        password: str = "testpassword123"
    ) -> dict:
        return {
            "email": email,
            "password": password
        }
    
    @staticmethod
    def create_register_request(
        email: str = "newuser@example.com",
        password: str = "newpassword123",
        name: str = "New User",
        role: str = "student"
    ) -> dict:
        return {
            "email": email,
            "password": password,
            "name": name,
            "role": role
        }

@pytest.fixture
def test_data() -> TestDataFactory:
    return TestDataFactory()