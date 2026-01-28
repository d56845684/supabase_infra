from fastapi import Depends, Request
from typing import Optional
from app.services.session_service import session_service
from app.services.permission_service import permission_service
from app.core.security import get_token_from_request, decode_token, TokenType
from app.core.exceptions import (
    AuthException, InvalidTokenException,
    SessionExpiredException, PermissionDeniedException
)
from app.models.session import SessionData


class CurrentUser:
    """當前用戶資訊"""

    def __init__(
        self,
        user_id: str,
        email: str,
        role: str,
        session_id: str,
        session_data: SessionData,
        employee_type: Optional[str] = None,
        permission_level: int = 0
    ):
        self.user_id = user_id
        self.email = email
        self.role = role
        self.session_id = session_id
        self.session_data = session_data
        self.employee_type = employee_type
        self.permission_level = permission_level

    def is_admin(self) -> bool:
        """檢查是否為管理員（權限等級 100）"""
        return self.permission_level >= 100

    def is_staff(self) -> bool:
        """檢查是否為員工（含管理員）"""
        return self.role in ["admin", "employee"]

    def is_teacher(self) -> bool:
        """檢查是否為教師"""
        return self.role == "teacher"

    def is_student(self) -> bool:
        """檢查是否為學生"""
        return self.role == "student"

    def has_permission(self, required_level: int) -> bool:
        """檢查是否有足夠的權限等級"""
        return self.permission_level >= required_level

    def is_full_time_or_above(self) -> bool:
        """檢查是否為正式員工以上（等級 >= 30）"""
        return self.permission_level >= 30

    def is_part_time_or_above(self) -> bool:
        """檢查是否為兼職員工以上（等級 >= 20）"""
        return self.permission_level >= 20

    def is_intern_or_above(self) -> bool:
        """檢查是否為工讀生以上（等級 >= 10）"""
        return self.permission_level >= 10

    def can_manage(self, target_employee_type: Optional[str]) -> bool:
        """檢查是否可以管理指定類型的員工"""
        return permission_service.can_manage(self.employee_type, target_employee_type)


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

    # 7. 取得權限等級（從 token 或查詢）
    user_id = payload.get("sub")
    employee_type = payload.get("employee_type")
    permission_level = payload.get("permission_level", 0)

    # 如果 token 中沒有權限資訊，從服務查詢
    if permission_level == 0 and payload.get("role") in ["admin", "employee"]:
        permission_level = await permission_service.get_user_permission_level(user_id)
        if not employee_type:
            employee_type = await permission_service.get_user_employee_type(user_id)

    return CurrentUser(
        user_id=user_id,
        email=payload.get("email", ""),
        role=payload.get("role", "student"),
        session_id=session_id,
        session_data=session_data,
        employee_type=employee_type,
        permission_level=permission_level
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


def require_permission_level(min_level: int):
    """
    權限等級檢查裝飾器

    Args:
        min_level: 所需的最低權限等級
            - 10: 工讀生
            - 20: 兼職員工
            - 30: 正式員工
            - 100: 管理員
    """
    async def permission_checker(
        current_user: CurrentUser = Depends(get_current_user)
    ) -> CurrentUser:
        # 非員工角色無權限等級
        if current_user.role not in ['admin', 'employee']:
            raise PermissionDeniedException("此操作需要員工權限")

        if current_user.permission_level < min_level:
            level_name = permission_service.get_level_name(min_level)
            raise PermissionDeniedException(
                f"權限不足，需要 {level_name} 以上權限"
            )
        return current_user
    return permission_checker


# 預定義的角色依賴
require_admin = require_role("admin")
require_staff = require_role("admin", "employee")
require_teacher = require_role("admin", "employee", "teacher")
require_authenticated = get_current_user

# 預定義的權限等級依賴
require_intern_level = require_permission_level(10)      # 工讀生以上
require_part_time_level = require_permission_level(20)   # 兼職員工以上
require_full_time_level = require_permission_level(30)   # 正式員工以上
require_admin_level = require_permission_level(100)      # 管理員
