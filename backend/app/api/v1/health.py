from fastapi import APIRouter
from app.services.redis_service import redis_service
from app.services.supabase_service import supabase_service
from app.schemas.response import BaseResponse
from datetime import datetime

router = APIRouter(prefix="/health", tags=["健康檢查"])

@router.get("/", response_model=dict)
async def health_check():
    """基本健康檢查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/ready", response_model=dict)
async def readiness_check():
    """就緒檢查（含依賴服務）"""
    checks = {
        "redis": False,
        "supabase": False
    }
    
    # 檢查 Redis
    try:
        await redis_service.client.ping()
        checks["redis"] = True
    except:
        pass
    
    # 檢查 Supabase
    try:
        result = await supabase_service.table_select(
            table="courses",
            columns="id",
            use_service_key=True
        )
        checks["supabase"] = True
    except:
        pass
    
    all_healthy = all(checks.values())
    
    return {
        "status": "ready" if all_healthy else "degraded",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }