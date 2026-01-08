from datetime import datetime, timezone
from typing import Optional, List
from app.services.redis_service import redis_service
from app.core.security import generate_session_id, hash_session_id
from app.config import settings
from app.models.session import SessionData
import json

class SessionService:
    # Redis Key 前綴
    SESSION_PREFIX = "session:"
    USER_SESSIONS_PREFIX = "user_sessions:"
    BLACKLIST_PREFIX = "blacklist:"
    
    def __init__(self):
        self.redis = redis_service
    
    # ========== Session 管理 ==========
    
    async def create_session(
        self,
        user_id: str,
        user_role: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        extra_data: Optional[dict] = None
    ) -> tuple[str, SessionData]:
        """建立新 Session"""
        session_id = generate_session_id()
        session_hash = hash_session_id(session_id)
        
        session_data = SessionData(
            session_id=session_hash,
            user_id=user_id,
            user_role=user_role,
            user_agent=user_agent,
            ip_address=ip_address,
            created_at=datetime.now(timezone.utc).isoformat(),
            last_activity=datetime.now(timezone.utc).isoformat(),
            extra_data=extra_data or {}
        )
        
        # 儲存 Session
        session_key = f"{self.SESSION_PREFIX}{session_hash}"
        await self.redis.set_json(
            session_key,
            session_data.model_dump(),
            expire_seconds=settings.SESSION_EXPIRE_MINUTES * 60
        )
        
        # 記錄用戶的所有 Sessions
        user_sessions_key = f"{self.USER_SESSIONS_PREFIX}{user_id}"
        await self.redis.sadd(user_sessions_key, session_hash)
        await self.redis.expire(
            user_sessions_key, 
            settings.SESSION_EXPIRE_MINUTES * 60
        )
        
        return session_id, session_data
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """取得 Session 資料"""
        session_hash = hash_session_id(session_id)
        session_key = f"{self.SESSION_PREFIX}{session_hash}"
        
        data = await self.redis.get_json(session_key)
        if not data:
            return None
        
        return SessionData(**data)
    
    async def update_session_activity(self, session_id: str) -> bool:
        """更新 Session 最後活動時間"""
        session_hash = hash_session_id(session_id)
        session_key = f"{self.SESSION_PREFIX}{session_hash}"
        
        data = await self.redis.get_json(session_key)
        if not data:
            return False
        
        data["last_activity"] = datetime.now(timezone.utc).isoformat()
        await self.redis.set_json(
            session_key,
            data,
            expire_seconds=settings.SESSION_EXPIRE_MINUTES * 60
        )
        return True
    
    async def destroy_session(self, session_id: str) -> bool:
        """銷毀 Session"""
        session_hash = hash_session_id(session_id)
        session_key = f"{self.SESSION_PREFIX}{session_hash}"
        
        # 取得 Session 資料以獲取 user_id
        data = await self.redis.get_json(session_key)
        if data:
            user_id = data.get("user_id")
            if user_id:
                # 從用戶 Sessions 集合中移除
                user_sessions_key = f"{self.USER_SESSIONS_PREFIX}{user_id}"
                await self.redis.srem(user_sessions_key, session_hash)
        
        # 刪除 Session
        await self.redis.delete(session_key)
        return True
    
    async def destroy_all_user_sessions(self, user_id: str) -> int:
        """銷毀用戶所有 Sessions (登出所有裝置)"""
        user_sessions_key = f"{self.USER_SESSIONS_PREFIX}{user_id}"
        session_hashes = await self.redis.smembers(user_sessions_key)
        
        count = 0
        for session_hash in session_hashes:
            session_key = f"{self.SESSION_PREFIX}{session_hash}"
            await self.redis.delete(session_key)
            count += 1
        
        await self.redis.delete(user_sessions_key)
        return count
    
    async def get_user_sessions(self, user_id: str) -> List[SessionData]:
        """取得用戶所有活躍 Sessions"""
        user_sessions_key = f"{self.USER_SESSIONS_PREFIX}{user_id}"
        session_hashes = await self.redis.smembers(user_sessions_key)
        
        sessions = []
        for session_hash in session_hashes:
            session_key = f"{self.SESSION_PREFIX}{session_hash}"
            data = await self.redis.get_json(session_key)
            if data:
                sessions.append(SessionData(**data))
        
        return sessions
    
    # ========== Token 黑名單 ==========
    
    async def blacklist_token(self, token: str, expire_seconds: int) -> bool:
        """將 Token 加入黑名單"""
        key = f"{self.BLACKLIST_PREFIX}{hash_session_id(token)}"
        return await self.redis.set(key, "1", expire_seconds=expire_seconds)
    
    async def is_token_blacklisted(self, token: str) -> bool:
        """檢查 Token 是否在黑名單中"""
        key = f"{self.BLACKLIST_PREFIX}{hash_session_id(token)}"
        return await self.redis.exists(key)
session_service = SessionService()