from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CourseBase(BaseModel):
    course_code: str = Field(..., min_length=1, max_length=50, description="課程代碼")
    course_name: str = Field(..., min_length=1, max_length=200, description="課程名稱")
    description: Optional[str] = Field(None, description="課程描述")
    duration_minutes: int = Field(60, ge=15, le=480, description="課程時長（分鐘）")
    is_active: bool = Field(True, description="是否啟用")


class CourseCreate(CourseBase):
    """建立課程的請求"""
    pass


class CourseUpdate(BaseModel):
    """更新課程的請求"""
    course_code: Optional[str] = Field(None, min_length=1, max_length=50)
    course_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=15, le=480)
    is_active: Optional[bool] = None


class CourseResponse(CourseBase):
    """課程回應"""
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CourseListResponse(BaseModel):
    """課程列表回應"""
    success: bool = True
    data: list[CourseResponse] = []
    total: int = 0
    page: int = 1
    per_page: int = 20
    total_pages: int = 0
