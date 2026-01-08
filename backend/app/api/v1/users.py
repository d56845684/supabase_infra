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
    
    # 查詢 user_profile
    profiles = await supabase_service.table_select(
        table="user_profiles",
        columns="*",
        filters={"id": current_user.user_id},
        use_service_key=True
    )
    
    entity_data = {}
    if profiles and len(profiles) > 0:
        profile = profiles[0]
        entity_id = profile.get(f"{table.rstrip('s')}_id")
        
        if entity_id:
            entities = await supabase_service.table_select(
                table=table,
                columns="*",
                filters={"id": entity_id},
                use_service_key=True
            )
            if entities:
                entity_data = entities[0]
    
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

@router.get("/", response_model=PaginatedResponse[UserProfile])
async def list_users(
    page: int = 1,
    per_page: int = 20,
    role: str = None,
    current_user: CurrentUser = Depends(require_staff)
):
    """列出所有用戶（僅限員工）"""
    filters = {}
    if role:
        filters["role"] = role
    
    # 查詢 user_profiles
    profiles = await supabase_service.table_select(
        table="user_profiles",
        columns="*",
        filters=filters if filters else None,
        use_service_key=True
    )
    
    # 分頁處理
    total = len(profiles)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_profiles = profiles[start:end]
    
    users = []
    for item in paginated_profiles:
        users.append(UserProfile(
            id=item["id"],
            email="",  # 需要額外查詢
            role=item.get("role", "student"),
            name=None,
            is_active=True
        ))
    
    total_pages = (total + per_page - 1) // per_page
    
    return PaginatedResponse(
        data=users,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )
