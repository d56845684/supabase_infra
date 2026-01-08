from typing import Optional, Tuple
from fastapi import Request, Response
from app.services.supabase_service import supabase_service
from app.services.session_service import session_service
from app.services.redis_service import redis_service
from app.core.security import (
    create_token, decode_token, verify_supabase_token,
    set_auth_cookies, clear_auth_cookies, TokenType
)
from app.core.exceptions import (
    AuthException, InvalidTokenException, 
    SessionExpiredException, UserNotFoundException
)
from app.schemas.auth import TokenPair, UserInfo
from app.config import settings
from datetime import timedelta

class AuthService:
    def __init__(self):
        self.supabase = supabase_service
        self.session = session_service
        self.redis = redis_service
    
    # ========== 用戶快取 ==========
    
    async def _cache_user_profile(self, user_id: str, profile: dict) -> None:
        """快取用戶資料"""
        cache_key = f"user_profile:{user_id}"
        await self.redis.set_json(
            cache_key,
            profile,
            expire_seconds=300  # 5 分鐘
        )
    
    async def _get_cached_user_profile(self, user_id: str) -> Optional[dict]:
        """取得快取的用戶資料"""
        cache_key = f"user_profile:{user_id}"
        return await self.redis.get_json(cache_key)
    
    async def _invalidate_user_cache(self, user_id: str) -> None:
        """清除用戶快取"""
        cache_key = f"user_profile:{user_id}"
        await self.redis.delete(cache_key)
    
    # ========== 登入/登出 ==========
    
    async def login(
        self,
        email: str,
        password: str,
        request: Request,
        response: Response
    ) -> Tuple[UserInfo, TokenPair]:
        """用戶登入"""
        # 1. Supabase 認證
        try:
            auth_response = self.supabase.sign_in_with_password(email, password)
        except Exception as e:
            raise AuthException(f"登入失敗: {str(e)}")
        
        user = auth_response.user
        session = auth_response.session
        
        if not user or not session:
            raise AuthException("登入失敗：無效的憑證")
        
        # 2. 取得用戶角色 (從 user_profiles 表)
        user_role = await self._get_user_role(user.id)
        
        # 3. 建立 Session
        session_id, session_data = await self.session.create_session(
            user_id=user.id,
            user_role=user_role,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
            extra_data={"email": user.email}
        )
        
        # 4. 建立自己的 JWT Token
        token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user_role,
            "session_id": session_data.session_id
        }
        
        access_token = create_token(token_data, TokenType.ACCESS)
        refresh_token = create_token(
            {"sub": user.id, "session_id": session_data.session_id},
            TokenType.REFRESH
        )
        
        # 5. 設定 HttpOnly Cookies
        set_auth_cookies(response, access_token, refresh_token, session_id)
        
        # 6. 快取用戶資料
        user_info = UserInfo(
            id=user.id,
            email=user.email,
            role=user_role,
            email_confirmed=user.email_confirmed_at is not None,
            created_at=user.created_at
        )
        await self._cache_user_profile(user.id, user_info.model_dump())
        
        token_pair = TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        return user_info, token_pair
    
    async def logout(
        self,
        request: Request,
        response: Response,
        logout_all_devices: bool = False
    ) -> bool:
        """用戶登出"""
        session_id = request.cookies.get("session_id")
        access_token = request.cookies.get("access_token")
        
        if session_id:
            session_data = await self.session.get_session(session_id)
            
            if session_data:
                if logout_all_devices:
                    # 登出所有裝置
                    await self.session.destroy_all_user_sessions(
                        session_data.user_id
                    )
                    await self._invalidate_user_cache(session_data.user_id)
                else:
                    # 只登出當前裝置
                    await self.session.destroy_session(session_id)
        
        # 將 Token 加入黑名單
        if access_token:
            await self.session.blacklist_token(
                access_token,
                settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
        
        # 清除 Cookies
        clear_auth_cookies(response)
        
        # Supabase 登出
        try:
            self.supabase.sign_out()
        except:
            pass
        
        return True
    
    async def refresh_tokens(
        self,
        request: Request,
        response: Response
    ) -> TokenPair:
        """刷新 Tokens"""
        refresh_token = request.cookies.get("refresh_token")
        session_id = request.cookies.get("session_id")
        
        if not refresh_token or not session_id:
            raise SessionExpiredException()
        
        # 驗證 Refresh Token
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != TokenType.REFRESH:
            raise InvalidTokenException()
        
        # 驗證 Session
        session_data = await self.session.get_session(session_id)
        if not session_data:
            raise SessionExpiredException()
        
        # 檢查 Token 是否在黑名單
        if await self.session.is_token_blacklisted(refresh_token):
            raise InvalidTokenException()
        
        user_id = payload.get("sub")
        
        # 取得用戶資料
        user_profile = await self._get_cached_user_profile(user_id)
        if not user_profile:
            user_role = await self._get_user_role(user_id)
            user_profile = {"role": user_role}
        
        # 建立新 Tokens
        token_data = {
            "sub": user_id,
            "role": user_profile.get("role", "student"),
            "session_id": session_data.session_id
        }
        
        new_access_token = create_token(token_data, TokenType.ACCESS)
        new_refresh_token = create_token(
            {"sub": user_id, "session_id": session_data.session_id},
            TokenType.REFRESH
        )
        
        # 將舊的 Refresh Token 加入黑名單
        await self.session.blacklist_token(
            refresh_token,
            settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )
        
        # 更新 Session 活動時間
        await self.session.update_session_activity(session_id)
        
        # 設定新 Cookies
        set_auth_cookies(response, new_access_token, new_refresh_token, session_id)
        
        return TokenPair(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    async def _get_user_role(self, user_id: str) -> str:
        """從資料庫取得用戶角色"""
        try:
            result = self.supabase.admin.table("user_profiles")\
                .select("role")\
                .eq("id", user_id)\
                .single()\
                .execute()
            
            if result.data:
                return result.data.get("role", "student")
        except:
            pass
        
        return "student"  # 預設角色

# 單例
auth_service = AuthService()