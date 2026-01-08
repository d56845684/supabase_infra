from fastapi import APIRouter, Depends
from app.core.dependencies import (
    get_current_user, require_staff, require_admin, CurrentUser
)
from app.services.supabase_service import supabase_service
from app.schemas.response import DataResponse, PaginatedResponse
from app.schemas.user import UserProfile
from typing import List

router = APIRouter(prefix="/users", tags=["用戶管理"])

@router.get("/profile", response_model=DataResponse[UserProfile])
async def get_profile(
    current_user: CurrentUser = Depends(get_current_user)
):
    """取得當前用戶完整資料"""
    # 根據角色查詢對應的表
    if current_user.role == "student":
        table = "students"
    elif current_user.role == "teacher":
        table = "teachers"
    else:
        table = "employees"
    
    result = supabase_service.admin.table("user_profiles")\
        .select(f"*, {table}(*)")\
        .eq("id", current_user.user_id)\
        .single()\
        .execute()
    
    if result.data:
        profile_data = result.data
        entity_data = profile_data.get(table, {}) or {}
        
        return DataResponse(
            data=UserProfile(
                id=current_user.user_id,
                email=current_user.email,
                role=current_user.role,
                name=entity_data.get("name"),
                avatar_url=entity_data.get("avatar_url"),
                is_active=entity_data.get("is_active", True)
            )
        )
    
    return DataResponse(data=None)

@router.get("/", response_model=PaginatedResponse[UserProfile])
async def list_users(
    page: int = 1,
    per_page: int = 20,
    role: str = None,
    current_user: CurrentUser = Depends(require_staff)
):
    """列出所有用戶（僅限員工）"""
    query = supabase_service.admin.table("user_profiles").select(
        "id, role, students(name, email, is_active), "
        "teachers(name, email, is_active), employees(name, email, is_active)",
        count="exact"
    )
    
    if role:
        query = query.eq("role", role)
    
    # 分頁
    offset = (page - 1) * per_page
    query = query.range(offset, offset + per_page - 1)
    
    result = query.execute()
    
    users = []
    for item in result.data:
        entity = item.get("students") or item.get("teachers") or item.get("employees") or {}
        users.append(UserProfile(
            id=item["id"],
            email=entity.get("email", ""),
            role=item["role"],
            name=entity.get("name"),
            is_active=entity.get("is_active", True)
        ))
    
    total = result.count or 0
    total_pages = (total + per_page - 1) // per_page
    
    return PaginatedResponse(
        data=users,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )
