from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Response, Request
from app.config import settings
import secrets
import hashlib

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token 類型
class TokenType:
    ACCESS = "access"
    REFRESH = "refresh"

def create_token(
    data: dict,
    token_type: str = TokenType.ACCESS,
    expires_delta: Optional[timedelta] = None
) -> str:
    """建立 JWT Token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    elif token_type == TokenType.ACCESS:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": token_type
    })
    
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm="HS256"
    )

def decode_token(token: str) -> Optional[dict]:
    """解碼 JWT Token"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload
    except JWTError:
        return None

def verify_supabase_token(token: str) -> Optional[dict]:
    """驗證 Supabase JWT Token"""
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )
        return payload
    except JWTError:
        return None

def generate_session_id() -> str:
    """生成安全的 Session ID"""
    return secrets.token_urlsafe(32)

def hash_session_id(session_id: str) -> str:
    """雜湊 Session ID 用於儲存"""
    return hashlib.sha256(session_id.encode()).hexdigest()

# ============================================
# Cookie 操作
# ============================================

def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    session_id: str
) -> None:
    """設定認證 Cookies (HttpOnly)"""
    
    # Access Token Cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN if settings.is_production else None
    )
    
    # Refresh Token Cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN if settings.is_production else None,
        path="/api/v1/auth"  # 限制路徑
    )
    
    # Session ID Cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        max_age=settings.SESSION_EXPIRE_MINUTES * 60,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN if settings.is_production else None
    )

def clear_auth_cookies(response: Response) -> None:
    """清除認證 Cookies"""
    cookie_settings = {
        "httponly": settings.COOKIE_HTTPONLY,
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
        "domain": settings.COOKIE_DOMAIN if settings.is_production else None
    }
    
    response.delete_cookie(key="access_token", **cookie_settings)
    response.delete_cookie(key="refresh_token", path="/api/v1/auth", **cookie_settings)
    response.delete_cookie(key="session_id", **cookie_settings)

def get_token_from_request(request: Request) -> Optional[str]:
    """從 Request 取得 Token (Cookie 或 Header)"""
    # 優先從 Cookie 取得
    token = request.cookies.get("access_token")
    if token:
        return token
    
    # 備用從 Authorization Header 取得
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]
    
    return None