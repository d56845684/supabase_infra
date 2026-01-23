"""
Line 綁定服務 - 管理 Line 帳號綁定
支援多頻道（學生/老師/員工使用不同 Channel）
"""
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime, timezone

from app.config import ChannelType
from app.services.supabase_service import supabase_service
from app.services.line_oauth_service import LineProfile


@dataclass
class LineBinding:
    """Line 綁定資料"""
    id: str
    user_id: str
    line_user_id: str
    line_display_name: Optional[str]
    line_picture_url: Optional[str]
    line_email: Optional[str]
    binding_status: str
    channel_type: str
    notify_booking_confirmation: bool
    notify_booking_reminder: bool
    notify_status_update: bool
    bound_at: datetime
    created_at: datetime


@dataclass
class NotificationPreferences:
    """通知偏好設定"""
    notify_booking_confirmation: bool = True
    notify_booking_reminder: bool = True
    notify_status_update: bool = True


class LineBindingService:
    """Line 綁定管理服務（多頻道支援）"""

    async def create_binding(
        self,
        user_id: str,
        profile: LineProfile,
        channel_type: ChannelType,
    ) -> LineBinding:
        """
        建立 Line 綁定

        Args:
            user_id: 用戶 ID
            profile: Line 用戶資料
            channel_type: 頻道類型

        Returns:
            綁定資料

        Raises:
            Exception: 如果綁定失敗
        """
        # 檢查是否已經綁定其他帳號（在同一頻道）
        existing = await self.get_binding_by_line_id(profile.user_id, channel_type)
        if existing and existing.user_id != user_id:
            raise Exception("此 Line 帳號已綁定其他用戶")

        # 檢查用戶是否已有綁定（在同一頻道）
        user_binding = await self.get_binding_by_user(user_id, channel_type)
        if user_binding:
            # 更新現有綁定
            return await self.update_binding(
                user_id=user_id,
                channel_type=channel_type,
                line_user_id=profile.user_id,
                line_display_name=profile.display_name,
                line_picture_url=profile.picture_url,
                line_email=profile.email,
                binding_status="active"
            )

        # 建立新綁定
        data = {
            "user_id": user_id,
            "line_user_id": profile.user_id,
            "line_display_name": profile.display_name,
            "line_picture_url": profile.picture_url,
            "line_email": profile.email,
            "binding_status": "active",
            "channel_type": channel_type,
        }

        result = await supabase_service.table_insert(
            table="line_user_bindings",
            data=data,
            use_service_key=True
        )

        return self._to_binding(result)

    async def get_binding_by_user(
        self,
        user_id: str,
        channel_type: Optional[ChannelType] = None
    ) -> Optional[LineBinding]:
        """
        透過用戶 ID 取得綁定

        Args:
            user_id: 用戶 ID
            channel_type: 頻道類型（若未指定則返回任一綁定）

        Returns:
            綁定資料，如果不存在則返回 None
        """
        try:
            filters = {"user_id": f"eq.{user_id}"}
            if channel_type:
                filters["channel_type"] = f"eq.{channel_type}"

            result = await supabase_service.table_select(
                table="line_user_bindings",
                select="*",
                filters=filters,
                use_service_key=True
            )

            if result and len(result) > 0:
                return self._to_binding(result[0])
            return None
        except Exception:
            return None

    async def get_all_bindings_by_user(self, user_id: str) -> List[LineBinding]:
        """
        取得用戶所有頻道的綁定

        Args:
            user_id: 用戶 ID

        Returns:
            綁定列表
        """
        try:
            result = await supabase_service.table_select(
                table="line_user_bindings",
                select="*",
                filters={"user_id": f"eq.{user_id}"},
                use_service_key=True
            )

            if result:
                return [self._to_binding(r) for r in result]
            return []
        except Exception:
            return []

    async def get_binding_by_line_id(
        self,
        line_user_id: str,
        channel_type: ChannelType
    ) -> Optional[LineBinding]:
        """
        透過 Line User ID 取得綁定

        Args:
            line_user_id: Line 用戶 ID
            channel_type: 頻道類型

        Returns:
            綁定資料，如果不存在則返回 None
        """
        try:
            result = await supabase_service.table_select(
                table="line_user_bindings",
                select="*",
                filters={
                    "line_user_id": f"eq.{line_user_id}",
                    "channel_type": f"eq.{channel_type}"
                },
                use_service_key=True
            )

            if result and len(result) > 0:
                return self._to_binding(result[0])
            return None
        except Exception:
            return None

    async def update_binding(
        self,
        user_id: str,
        channel_type: ChannelType,
        **updates
    ) -> Optional[LineBinding]:
        """
        更新綁定資料

        Args:
            user_id: 用戶 ID
            channel_type: 頻道類型
            **updates: 要更新的欄位

        Returns:
            更新後的綁定資料
        """
        try:
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()

            result = await supabase_service.table_update(
                table="line_user_bindings",
                data=updates,
                filters={
                    "user_id": f"eq.{user_id}",
                    "channel_type": f"eq.{channel_type}"
                },
                use_service_key=True
            )

            if result and len(result) > 0:
                return self._to_binding(result[0])
            return None
        except Exception:
            return None

    async def unbind(
        self,
        user_id: str,
        channel_type: ChannelType
    ) -> bool:
        """
        解除 Line 綁定

        Args:
            user_id: 用戶 ID
            channel_type: 頻道類型

        Returns:
            True 如果成功
        """
        try:
            await supabase_service.table_update(
                table="line_user_bindings",
                data={
                    "binding_status": "unlinked",
                    "unbound_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
                filters={
                    "user_id": f"eq.{user_id}",
                    "channel_type": f"eq.{channel_type}"
                },
                use_service_key=True
            )
            return True
        except Exception:
            return False

    async def update_notification_preferences(
        self,
        user_id: str,
        channel_type: ChannelType,
        preferences: NotificationPreferences
    ) -> bool:
        """
        更新通知偏好設定

        Args:
            user_id: 用戶 ID
            channel_type: 頻道類型
            preferences: 通知偏好設定

        Returns:
            True 如果成功
        """
        try:
            await supabase_service.table_update(
                table="line_user_bindings",
                data={
                    "notify_booking_confirmation": preferences.notify_booking_confirmation,
                    "notify_booking_reminder": preferences.notify_booking_reminder,
                    "notify_status_update": preferences.notify_status_update,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
                filters={
                    "user_id": f"eq.{user_id}",
                    "channel_type": f"eq.{channel_type}"
                },
                use_service_key=True
            )
            return True
        except Exception:
            return False

    async def get_notification_preferences(
        self,
        user_id: str,
        channel_type: ChannelType
    ) -> Optional[NotificationPreferences]:
        """
        取得通知偏好設定

        Args:
            user_id: 用戶 ID
            channel_type: 頻道類型

        Returns:
            通知偏好設定
        """
        binding = await self.get_binding_by_user(user_id, channel_type)
        if not binding:
            return None

        return NotificationPreferences(
            notify_booking_confirmation=binding.notify_booking_confirmation,
            notify_booking_reminder=binding.notify_booking_reminder,
            notify_status_update=binding.notify_status_update,
        )

    async def get_line_user_id(
        self,
        user_id: str,
        channel_type: ChannelType
    ) -> Optional[str]:
        """
        取得用戶的 Line User ID

        Args:
            user_id: 用戶 ID
            channel_type: 頻道類型

        Returns:
            Line User ID，如果未綁定則返回 None
        """
        binding = await self.get_binding_by_user(user_id, channel_type)
        if binding and binding.binding_status == "active":
            return binding.line_user_id
        return None

    async def is_bound(
        self,
        user_id: str,
        channel_type: Optional[ChannelType] = None
    ) -> bool:
        """
        檢查用戶是否已綁定 Line

        Args:
            user_id: 用戶 ID
            channel_type: 頻道類型（若未指定則檢查任一頻道）

        Returns:
            True 如果已綁定
        """
        binding = await self.get_binding_by_user(user_id, channel_type)
        return binding is not None and binding.binding_status == "active"

    def _to_binding(self, data: dict) -> LineBinding:
        """將字典轉換為 LineBinding 物件"""
        return LineBinding(
            id=data["id"],
            user_id=data["user_id"],
            line_user_id=data["line_user_id"],
            line_display_name=data.get("line_display_name"),
            line_picture_url=data.get("line_picture_url"),
            line_email=data.get("line_email"),
            binding_status=data.get("binding_status", "active"),
            channel_type=data.get("channel_type", "student"),
            notify_booking_confirmation=data.get("notify_booking_confirmation", True),
            notify_booking_reminder=data.get("notify_booking_reminder", True),
            notify_status_update=data.get("notify_status_update", True),
            bound_at=data.get("bound_at", data.get("created_at")),
            created_at=data.get("created_at"),
        )


# 單例
line_binding_service = LineBindingService()
