from fastapi import APIRouter, Depends, Query, HTTPException
from app.services.supabase_service import supabase_service
from app.core.dependencies import get_current_user, CurrentUser, require_staff
from app.schemas.course import (
    CourseCreate, CourseUpdate, CourseResponse, CourseListResponse
)
from app.schemas.response import BaseResponse, DataResponse
from typing import Optional
import math

router = APIRouter(prefix="/courses", tags=["課程管理"])


@router.get("", response_model=CourseListResponse)
async def list_courses(
    page: int = Query(1, ge=1, description="頁碼"),
    per_page: int = Query(20, ge=1, le=100, description="每頁數量"),
    search: Optional[str] = Query(None, description="搜尋關鍵字（課程代碼或名稱）"),
    is_active: Optional[bool] = Query(None, description="篩選啟用狀態"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """取得課程列表"""
    try:
        # 建立基本查詢
        filters = {"is_deleted": "eq.false"}

        if is_active is not None:
            filters["is_active"] = f"eq.{str(is_active).lower()}"

        # 取得總數
        all_courses = await supabase_service.table_select(
            table="courses",
            select="id",
            filters=filters,
            use_service_key=True
        )
        total = len(all_courses)

        # 計算分頁
        total_pages = math.ceil(total / per_page) if total > 0 else 1
        offset = (page - 1) * per_page

        # 取得分頁資料
        courses = await supabase_service.table_select_with_pagination(
            table="courses",
            select="id,course_code,course_name,description,duration_minutes,is_active,created_at,updated_at",
            filters=filters,
            order_by="created_at.desc",
            limit=per_page,
            offset=offset,
            use_service_key=True
        )

        # 如果有搜尋關鍵字，在結果中篩選（PostgREST 的 or 較複雜，這裡簡化處理）
        if search:
            search_lower = search.lower()
            courses = [
                c for c in courses
                if search_lower in c.get("course_code", "").lower()
                or search_lower in c.get("course_name", "").lower()
            ]

        return CourseListResponse(
            data=[CourseResponse(**c) for c in courses],
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得課程列表失敗: {str(e)}")


@router.get("/{course_id}", response_model=DataResponse[CourseResponse])
async def get_course(
    course_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """取得單一課程"""
    try:
        result = await supabase_service.table_select(
            table="courses",
            select="id,course_code,course_name,description,duration_minutes,is_active,created_at,updated_at",
            filters={"id": course_id, "is_deleted": "eq.false"},
            use_service_key=True
        )

        if not result:
            raise HTTPException(status_code=404, detail="課程不存在")

        return DataResponse(data=CourseResponse(**result[0]))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得課程失敗: {str(e)}")


@router.post("", response_model=DataResponse[CourseResponse])
async def create_course(
    data: CourseCreate,
    current_user: CurrentUser = Depends(require_staff)
):
    """建立課程（僅限員工）"""
    try:
        # 檢查課程代碼是否已存在
        existing = await supabase_service.table_select(
            table="courses",
            select="id",
            filters={"course_code": data.course_code, "is_deleted": "eq.false"},
            use_service_key=True
        )

        if existing:
            raise HTTPException(status_code=400, detail="課程代碼已存在")

        # 建立課程
        course_data = data.model_dump()

        result = await supabase_service.table_insert(
            table="courses",
            data=course_data,
            use_service_key=True
        )

        if not result:
            raise HTTPException(status_code=500, detail="建立課程失敗")

        # table_insert 返回單個 dict 而不是 list
        return DataResponse(
            message="課程建立成功",
            data=CourseResponse(**result)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"建立課程失敗: {str(e)}")


@router.put("/{course_id}", response_model=DataResponse[CourseResponse])
async def update_course(
    course_id: str,
    data: CourseUpdate,
    current_user: CurrentUser = Depends(require_staff)
):
    """更新課程（僅限員工）"""
    try:
        # 檢查課程是否存在
        existing = await supabase_service.table_select(
            table="courses",
            select="id,course_code",
            filters={"id": course_id, "is_deleted": "eq.false"},
            use_service_key=True
        )

        if not existing:
            raise HTTPException(status_code=404, detail="課程不存在")

        # 如果更新課程代碼，檢查是否重複
        if data.course_code and data.course_code != existing[0]["course_code"]:
            duplicate = await supabase_service.table_select(
                table="courses",
                select="id",
                filters={"course_code": data.course_code, "is_deleted": "eq.false"},
                use_service_key=True
            )
            if duplicate:
                raise HTTPException(status_code=400, detail="課程代碼已存在")

        # 更新課程
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}

        if not update_data:
            raise HTTPException(status_code=400, detail="沒有要更新的資料")

        result = await supabase_service.table_update(
            table="courses",
            data=update_data,
            filters={"id": course_id},
            use_service_key=True
        )

        if not result:
            raise HTTPException(status_code=500, detail="更新課程失敗")

        # table_update 返回單個 dict 而不是 list
        return DataResponse(
            message="課程更新成功",
            data=CourseResponse(**result)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新課程失敗: {str(e)}")


@router.delete("/{course_id}", response_model=BaseResponse)
async def delete_course(
    course_id: str,
    current_user: CurrentUser = Depends(require_staff)
):
    """刪除課程（軟刪除，僅限員工）"""
    try:
        # 檢查課程是否存在
        existing = await supabase_service.table_select(
            table="courses",
            select="id",
            filters={"id": course_id, "is_deleted": "eq.false"},
            use_service_key=True
        )

        if not existing:
            raise HTTPException(status_code=404, detail="課程不存在")

        # 軟刪除
        from datetime import datetime
        result = await supabase_service.table_update(
            table="courses",
            data={
                "is_deleted": True,
                "deleted_at": datetime.utcnow().isoformat()
            },
            filters={"id": course_id},
            use_service_key=True
        )

        if not result:
            raise HTTPException(status_code=500, detail="刪除課程失敗")

        return BaseResponse(message="課程刪除成功")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刪除課程失敗: {str(e)}")
