from fastapi import Depends, Request
from typing import Optional
from app.services.session_service import session_service
from app.services.auth_service import auth_service
from app.core.security import get_token_from_request, decode_token, TokenType
from app.core.exceptions import (
    AuthException, InvalidTokenException, 
    SessionExpiredException, PermissionDeniedException
)
from app.models.session import SessionData
from app.schemas.user import UserProfile

class CurrentUser:
    """當前用戶資訊"""
    def __init__(
        self,
        user_id: str,
        email: str,
        role: str,
        session_id: str,
        session_data: SessionData
    ):
        self.user_id = user_id
        self.email = email
        self.role = role
        self.session_id = session_id
        self.session_data = session_data
    
    def is_admin(self) -> bool:
        return self.role == "admin"
    
    def is_staff(self) -> bool:
        return self.role in ["admin", "employee"]
    
    def is_teacher(self) -> bool:
        return self.role == "teacher"
    
    def is_student(self) -> bool:
        return self.role == "student"

async def get_current_user(request: Request) -> CurrentUser:
    """取得當前已認證的用戶"""
    # 1. 取得 Token
    token = get_token_from_request(request)
    if not token:
        raise AuthException("未提供認證資訊")
    
    # 2. 檢查 Token 是否在黑名單
    if await session_service.is_token_blacklisted(token):
        raise InvalidTokenException()
    
    # 3. 解碼 Token
    payload = decode_token(token)
    if not payload:
        raise InvalidTokenException()
    
    if payload.get("type") != TokenType.ACCESS:
        raise InvalidTokenException()
    
    # 4. 取得 Session
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise SessionExpiredException()
    
    session_data = await session_service.get_session(session_id)
    if not session_data:
        raise SessionExpiredException()
    
    # 5. 驗證 Session 與 Token 匹配
    if session_data.user_id != payload.get("sub"):
        raise InvalidTokenException()
    
    # 6. 更新 Session 活動時間
    await session_service.update_session_activity(session_id)
    
    return CurrentUser(
        user_id=payload.get("sub"),
        email=payload.get("email", ""),
        role=payload.get("role", "student"),
        session_id=session_id,
        session_data=session_data
    )

async def get_optional_user(request: Request) -> Optional[CurrentUser]:
    """取得當前用戶（可選，未登入返回 None）"""
    try:
        return await get_current_user(request)
    except:
        return None

def require_role(*allowed_roles: str):
    """角色權限檢查裝飾器"""
    async def role_checker(
        current_user: CurrentUser = Depends(get_current_user)
    ) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise PermissionDeniedException(
                f"需要以下角色之一: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker

# 預定義的角色依賴
require_admin = require_role("admin")
require_staff = require_role("admin", "employee")
require_teacher = require_role("admin", "employee", "teacher")
require_authenticated = get_current_user