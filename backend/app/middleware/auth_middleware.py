from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.services.session_service import session_service
from app.core.security import get_token_from_request, decode_token
from app.config import settings
import time
import logging

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    """認證中間件：處理 Token 驗證和 Session 追蹤"""
    
    # 不需要認證的路徑
    PUBLIC_PATHS = [
        "/api/v1/health",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/password/reset",
        "/api/v1/auth/refresh",
        "/docs",
        "/redoc",
        "/openapi.json"
    ]
    
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        
        # 檢查是否為公開路徑
        path = request.url.path
        is_public = any(path.startswith(p) for p in self.PUBLIC_PATHS)
        
        if not is_public:
            # 驗證 Token
            token = get_token_from_request(request)
            
            if token:
                # 檢查黑名單
                if await session_service.is_token_blacklisted(token):
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Token 已失效"}
                    )
                
                # 解碼並附加到 request.state
                payload = decode_token(token)
                if payload:
                    request.state.user_id = payload.get("sub")
                    request.state.user_role = payload.get("role")
        
        # 執行請求
        response = await call_next(request)
        
        # 記錄請求時間
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中間件"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # 取得客戶端 IP
        client_ip = request.client.host if request.client else "unknown"
        
        # 建立速率限制 key
        rate_key = f"rate_limit:{client_ip}"
        
        try:
            from app.services.redis_service import redis_service
            
            current = await redis_service.client.incr(rate_key)
            
            if current == 1:
                await redis_service.expire(rate_key, 60)
            
            if current > self.requests_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "請求過於頻繁，請稍後再試"}
                )
        except:
            # Redis 不可用時跳過速率限制
            pass
        
        return await call_next(request)
