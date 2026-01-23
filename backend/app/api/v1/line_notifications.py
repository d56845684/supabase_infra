"""
Line 通知 API 端點
支援多頻道（學生/老師/員工使用不同 Channel）
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.config import ChannelType
from app.services.line_binding_service import (
    line_binding_service,
    NotificationPreferences
)
from app.services.line_message_service import line_message_service
from app.services.supabase_service import supabase_service
from app.core.dependencies import get_current_user, require_staff, CurrentUser
from app.schemas.line import (
    NotificationPreferencesRequest,
    NotificationPreferencesResponse,
    TestNotificationRequest,
    TestNotificationResponse,
    NotificationLogItem,
    NotificationHistoryResponse,
)
from app.schemas.response import BaseResponse

router = APIRouter(prefix="/notifications/line", tags=["Line 通知"])


def get_channel_type_from_role(role: str) -> ChannelType:
    """根據用戶角色取得對應的頻道類型"""
    role_to_channel = {
        "student": "student",
        "teacher": "teacher",
        "employee": "employee",
        "admin": "employee",
    }
    return role_to_channel.get(role, "student")


@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    channel: ChannelType = Query(None, description="頻道類型（預設根據角色）"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    取得通知偏好設定
    """
    channel_type = channel or get_channel_type_from_role(current_user.role)

    preferences = await line_binding_service.get_notification_preferences(
        current_user.user_id,
        channel_type
    )

    if preferences:
        return NotificationPreferencesResponse(
            channel_type=channel_type,
            notify_booking_confirmation=preferences.notify_booking_confirmation,
            notify_booking_reminder=preferences.notify_booking_reminder,
            notify_status_update=preferences.notify_status_update,
        )
    else:
        # 未綁定 Line，返回預設值
        return NotificationPreferencesResponse(
            channel_type=channel_type,
            notify_booking_confirmation=True,
            notify_booking_reminder=True,
            notify_status_update=True,
        )


@router.put("/preferences", response_model=BaseResponse)
async def update_notification_preferences(
    data: NotificationPreferencesRequest,
    channel: ChannelType = Query(None, description="頻道類型（預設根據角色）"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    更新通知偏好設定
    """
    channel_type = channel or get_channel_type_from_role(current_user.role)

    # 檢查是否已綁定 Line
    is_bound = await line_binding_service.is_bound(current_user.user_id, channel_type)
    if not is_bound:
        return BaseResponse(
            success=False,
            message=f"尚未綁定 Line {channel_type} 頻道，無法設定通知偏好"
        )

    preferences = NotificationPreferences(
        notify_booking_confirmation=data.notify_booking_confirmation,
        notify_booking_reminder=data.notify_booking_reminder,
        notify_status_update=data.notify_status_update,
    )

    success = await line_binding_service.update_notification_preferences(
        current_user.user_id,
        channel_type,
        preferences
    )

    if success:
        return BaseResponse(message="通知偏好已更新")
    else:
        return BaseResponse(success=False, message="更新失敗")


@router.post("/test", response_model=TestNotificationResponse)
async def send_test_notification(
    data: TestNotificationRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    發送測試通知

    用於測試 Line 通知是否正常運作
    """
    channel_type = data.channel or get_channel_type_from_role(current_user.role)

    if not line_message_service.is_channel_configured(channel_type):
        return TestNotificationResponse(
            success=False,
            message=f"Line {channel_type} 頻道通知功能未啟用",
            channel_type=channel_type
        )

    # 檢查是否已綁定 Line
    is_bound = await line_binding_service.is_bound(current_user.user_id, channel_type)
    if not is_bound:
        return TestNotificationResponse(
            success=False,
            message=f"尚未綁定 Line {channel_type} 頻道，無法發送通知",
            channel_type=channel_type
        )

    success = await line_message_service.send_custom_notification(
        current_user.user_id,
        data.message,
        channel_type
    )

    if success:
        return TestNotificationResponse(
            success=True,
            message="測試通知已發送",
            channel_type=channel_type
        )
    else:
        return TestNotificationResponse(
            success=False,
            message="發送失敗",
            channel_type=channel_type
        )


@router.get("/history", response_model=NotificationHistoryResponse)
async def get_notification_history(
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(20, ge=1, le=100, description="每頁筆數"),
    channel: Optional[ChannelType] = Query(None, description="頻道類型篩選"),
    user_id: Optional[str] = Query(None, description="用戶 ID（僅員工可用）"),
    notification_type: Optional[str] = Query(None, description="通知類型"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    取得通知歷史

    一般用戶只能查看自己的歷史，員工可查看所有
    """
    # 決定查詢的 user_id
    query_user_id = current_user.user_id
    if user_id and current_user.is_staff():
        query_user_id = user_id
    elif user_id and not current_user.is_staff():
        query_user_id = current_user.user_id  # 忽略非員工的 user_id 參數

    # 建立查詢條件
    filters = {}
    if query_user_id and not (current_user.is_staff() and user_id is None):
        filters["user_id"] = f"eq.{query_user_id}"

    if channel:
        filters["channel_type"] = f"eq.{channel}"

    if notification_type:
        filters["notification_type"] = f"eq.{notification_type}"

    # 計算 offset
    offset = (page - 1) * page_size

    try:
        # 查詢總數
        count_result = await supabase_service.table_select(
            table="line_notification_logs",
            select="id",
            filters=filters,
            use_service_key=True
        )
        total = len(count_result) if count_result else 0

        # 查詢資料
        result = await supabase_service.table_select(
            table="line_notification_logs",
            select="*",
            filters=filters,
            order="created_at.desc",
            limit=page_size,
            offset=offset,
            use_service_key=True
        )

        items = [
            NotificationLogItem(
                id=item["id"],
                channel_type=item.get("channel_type", "student"),
                notification_type=item["notification_type"],
                notification_status=item["notification_status"],
                message_content=item.get("message_content"),
                reference_type=item.get("reference_type"),
                reference_id=item.get("reference_id"),
                sent_at=item.get("sent_at"),
                created_at=item["created_at"],
            )
            for item in (result or [])
        ]

        return NotificationHistoryResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception:
        return NotificationHistoryResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
        )
