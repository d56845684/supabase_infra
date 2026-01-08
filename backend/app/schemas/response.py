from pydantic import BaseModel
from typing import Optional, Any, Generic, TypeVar, List

T = TypeVar("T")

class BaseResponse(BaseModel):
    success: bool = True
    message: str = "操作成功"
    
class DataResponse(BaseResponse, Generic[T]):
    data: Optional[T] = None

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Any] = None

class PaginatedResponse(BaseResponse, Generic[T]):
    data: List[T] = []
    total: int = 0
    page: int = 1
    per_page: int = 20
    total_pages: int = 0