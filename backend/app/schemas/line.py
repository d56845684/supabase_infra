"""
Line 相關 Schemas
支援多頻道（學生/老師/員工使用不同 Channel）
"""
from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field

# 頻道類型
ChannelType = Literal["student", "teacher", "employee"]


# ============================================
# Line 綁定相關
# ============================================

class LineBindingStatus(BaseModel):
    """Line 綁定狀態"""
    is_bound: bool = Field(description="是否已綁定 Line")
    channel_type: Optional[str] = Field(None, description="頻道類型")
    line_display_name: Optional[str] = Field(None, description="Line 顯示名稱")
    line_picture_url: Optional[str] = Field(None, description="Line 頭像 URL")
    bound_at: Optional[datetime] = Field(None, description="綁定時間")
    bind_url: Optional[str] = Field(None, description="綁定 URL（未綁定時提供）")


class LineBindingResponse(BaseModel):
    """Line 綁定回應"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[LineBindingStatus] = None


class LineBindingsListResponse(BaseModel):
    """Line 綁定列表回應"""
    success: bool = True
    message: str = "操作成功"
    bindings: List[LineBindingStatus] = []


# ============================================
# 通知偏好相關
# ============================================

class NotificationPreferencesRequest(BaseModel):
    """更新通知偏好請求"""
    notify_booking_confirmation: bool = Field(True, description="預約確認通知")
    notify_booking_reminder: bool = Field(True, description="預約提醒通知")
    notify_status_update: bool = Field(True, description="狀態更新通知")


class NotificationPreferencesResponse(BaseModel):
    """通知偏好回應"""
    channel_type: str = Field(description="頻道類型")
    notify_booking_confirmation: bool
    notify_booking_reminder: bool
    notify_status_update: bool


# ============================================
# 測試通知
# ============================================

class TestNotificationRequest(BaseModel):
    """發送測試通知請求"""
    message: str = Field("這是一則測試通知", description="測試訊息內容")
    channel: Optional[ChannelType] = Field(None, description="頻道類型（預設根據角色）")


class TestNotificationResponse(BaseModel):
    """測試通知回應"""
    success: bool
    message: str
    channel_type: Optional[str] = None


# ============================================
# 通知歷史
# ============================================

class NotificationLogItem(BaseModel):
    """通知日誌項目"""
    id: str
    channel_type: str
    notification_type: str
    notification_status: str
    message_content: Optional[str]
    reference_type: Optional[str]
    reference_id: Optional[str]
    sent_at: Optional[datetime]
    created_at: datetime


class NotificationHistoryResponse(BaseModel):
    """通知歷史回應"""
    items: list[NotificationLogItem]
    total: int
    page: int
    page_size: int


# ============================================
# Line OAuth 相關
# ============================================

class LineLoginUrlResponse(BaseModel):
    """Line 登入 URL 回應"""
    url: str = Field(description="Line OAuth 授權 URL")
    state: str = Field(description="OAuth state（用於 CSRF 保護）")
    channel_type: str = Field(description="頻道類型")


class LineCallbackRequest(BaseModel):
    """Line OAuth 回調請求"""
    code: str = Field(description="授權碼")
    state: str = Field(description="OAuth state")


class LineUserInfo(BaseModel):
    """Line 用戶資訊"""
    line_user_id: str
    display_name: str
    picture_url: Optional[str]
    email: Optional[str]


class LineLoginResponse(BaseModel):
    """Line 登入回應"""
    success: bool = True
    message: str = "登入成功"
    is_new_user: bool = Field(False, description="是否為新建立的帳號")
    channel_type: str = Field(description="登入的頻道類型")
    line_info: Optional[LineUserInfo] = None
