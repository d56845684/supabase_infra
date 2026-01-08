import redis.asyncio as redis
from typing import Optional, Any
import json
from app.config import settings
from contextlib import asynccontextmanager

class RedisService:
    def __init__(self):
        self._pool: Optional[redis.ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
    
    async def connect(self) -> None:
        """建立 Redis 連線"""
        self._pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
            max_connections=10
        )
        self._client = redis.Redis(connection_pool=self._pool)
        # 測試連線
        await self._client.ping()
    
    async def disconnect(self) -> None:
        """關閉 Redis 連線"""
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()
    
    @property
    def client(self) -> redis.Redis:
        if not self._client:
            raise RuntimeError("Redis 尚未連線")
        return self._client
    
    # ========== 基本操作 ==========
    
    async def get(self, key: str) -> Optional[str]:
        """取得值"""
        return await self.client.get(key)
    
    async def set(
        self, 
        key: str, 
        value: str, 
        expire_seconds: Optional[int] = None
    ) -> bool:
        """設定值"""
        return await self.client.set(key, value, ex=expire_seconds)
    
    async def delete(self, key: str) -> int:
        """刪除鍵"""
        return await self.client.delete(key)
    
    async def exists(self, key: str) -> bool:
        """檢查鍵是否存在"""
        return await self.client.exists(key) > 0
    
    async def expire(self, key: str, seconds: int) -> bool:
        """設定過期時間"""
        return await self.client.expire(key, seconds)
    
    async def ttl(self, key: str) -> int:
        """取得剩餘存活時間"""
        return await self.client.ttl(key)
    
    # ========== JSON 操作 ==========
    
    async def get_json(self, key: str) -> Optional[dict]:
        """取得 JSON 物件"""
        data = await self.get(key)
        return json.loads(data) if data else None
    
    async def set_json(
        self, 
        key: str, 
        value: dict, 
        expire_seconds: Optional[int] = None
    ) -> bool:
        """設定 JSON 物件"""
        return await self.set(key, json.dumps(value), expire_seconds)
    
    # ========== Hash 操作 ==========
    
    async def hget(self, name: str, key: str) -> Optional[str]:
        return await self.client.hget(name, key)
    
    async def hset(self, name: str, key: str, value: str) -> int:
        return await self.client.hset(name, key, value)
    
    async def hgetall(self, name: str) -> dict:
        return await self.client.hgetall(name)
    
    async def hdel(self, name: str, *keys: str) -> int:
        return await self.client.hdel(name, *keys)
    
    # ========== Set 操作 (用於 Session 管理) ==========
    
    async def sadd(self, key: str, *values: str) -> int:
        return await self.client.sadd(key, *values)
    
    async def srem(self, key: str, *values: str) -> int:
        return await self.client.srem(key, *values)
    
    async def smembers(self, key: str) -> set:
        return await self.client.smembers(key)
    
    async def sismember(self, key: str, value: str) -> bool:
        return await self.client.sismember(key, value)

# 單例
redis_service = RedisService()