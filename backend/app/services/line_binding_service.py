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
    user_id: Optional[str]
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
        建立或更新 Line 綁定

        邏輯：
        1. 檢查此 Line UUID 是否已有記錄
        2. 如果有記錄且已綁定其他用戶（user_id 不為空且不同），拒絕綁定
        3. 如果有記錄但 user_id 為空（已解除綁定），更新 user_id
        4. 如果沒有記錄，建立新記錄

        Args:
            user_id: 用戶 ID
            profile: Line 用戶資料
            channel_type: 頻道類型

        Returns:
            綁定資料

        Raises:
            Exception: 如果綁定失敗
        """
        # 檢查是否已有此 Line UUID 的記錄（不論是否有綁定用戶）
        existing_line_record = await self._get_record_by_line_id(profile.user_id, channel_type)

        if existing_line_record:
            # 有記錄，檢查綁定狀態和用戶
            existing_user_id = existing_line_record.get("user_id")
            existing_status = existing_line_record.get("binding_status")

            # 只有當狀態為 active 且綁定給其他用戶時才拒絕
            if existing_status == "active" and existing_user_id and existing_user_id != user_id:
                raise Exception("此 Line 帳號已綁定其他用戶")

            # 更新現有記錄：
            # - 狀態為 unlinked：重新綁定（更新 user_id 和狀態）
            # - 狀態為 active 且同一用戶：更新資料
            # - user_id 為空：綁定到新用戶
            result = await supabase_service.table_update(
                table="line_user_bindings",
                data={
                    "user_id": user_id,
                    "line_display_name": profile.display_name,
                    "line_picture_url": profile.picture_url,
                    "line_email": profile.email,
                    "binding_status": "active",
                    "bound_at": datetime.now(timezone.utc).isoformat(),
                    "unbound_at": None,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
                filters={
                    "line_user_id": profile.user_id,
                    "channel_type": channel_type
                },
                use_service_key=True
            )
            return self._to_binding(result)

        # 沒有記錄，建立新綁定
        data = {
            "user_id": user_id,
            "line_user_id": profile.user_id,
            "line_display_name": profile.display_name,
            "line_picture_url": profile.picture_url,
            "line_email": profile.email,
            "binding_status": "active",
            "channel_type": channel_type,
            "bound_at": datetime.now(timezone.utc).isoformat(),
        }

        result = await supabase_service.table_insert(
            table="line_user_bindings",
            data=data,
            use_service_key=True
        )

        return self._to_binding(result)

    async def _get_record_by_line_id(
        self,
        line_user_id: str,
        channel_type: ChannelType
    ) -> Optional[dict]:
        """
        透過 Line User ID 取得記錄（不論綁定狀態）

        Args:
            line_user_id: Line 用戶 ID
            channel_type: 頻道類型

        Returns:
            原始記錄 dict，如果不存在則返回 None
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
                return result[0]
            return None
        except Exception:
            return None

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

    async def get_all_bindings_by_user(
        self,
        user_id: str,
        include_unlinked: bool = False
    ) -> List[LineBinding]:
        """
        取得用戶所有頻道的綁定

        Args:
            user_id: 用戶 ID
            include_unlinked: 是否包含已解除的綁定

        Returns:
            綁定列表
        """
        try:
            filters = {"user_id": f"eq.{user_id}"}
            if not include_unlinked:
                filters["binding_status"] = "eq.active"

            result = await supabase_service.table_select(
                table="line_user_bindings",
                select="*",
                filters=filters,
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
        透過 Line User ID 取得綁定（指定頻道）

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

    async def get_any_binding_by_line_id(
        self,
        line_user_id: str
    ) -> Optional[LineBinding]:
        """
        透過 Line User ID 取得任何綁定（不限頻道）

        用於檢查 Line 帳號是否已被任何用戶綁定

        Args:
            line_user_id: Line 用戶 ID

        Returns:
            綁定資料，如果不存在則返回 None
        """
        try:
            result = await supabase_service.table_select(
                table="line_user_bindings",
                select="*",
                filters={
                    "line_user_id": f"eq.{line_user_id}",
                    "binding_status": "eq.active"
                },
                use_service_key=True
            )

            if result and len(result) > 0:
                return self._to_binding(result[0])
            return None
        except Exception:
            return None

    async def is_line_id_bound_to_other_user(
        self,
        line_user_id: str,
        current_user_id: str
    ) -> tuple[bool, Optional[LineBinding]]:
        """
        檢查 Line 帳號是否已綁定給其他用戶

        Args:
            line_user_id: Line 用戶 ID
            current_user_id: 當前用戶 ID

        Returns:
            (是否已綁定給其他用戶, 現有綁定資料)
        """
        try:
            result = await supabase_service.table_select(
                table="line_user_bindings",
                select="*",
                filters={
                    "line_user_id": f"eq.{line_user_id}",
                    "binding_status": "eq.active"
                },
                use_service_key=True
            )

            if result and len(result) > 0:
                binding = self._to_binding(result[0])
                if binding.user_id != current_user_id:
                    return True, binding
            return False, None
        except Exception:
            return False, None

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

        將 user_id 設為 NULL，保留 Line UUID 記錄。
        下次綁定時可重新關聯用戶。

        Args:
            user_id: 用戶 ID
            channel_type: 頻道類型

        Returns:
            True 如果成功
        """
        try:
            # 注意：table_update 會自動加上 eq. 前綴
            # 設定 user_id 為 None (NULL)，保留 Line UUID 記錄
            result = await supabase_service.table_update(
                table="line_user_bindings",
                data={
                    "user_id": None,  # 清除 user_id，保留 Line UUID 記錄
                    "binding_status": "unlinked",
                    "unbound_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
                filters={
                    "user_id": user_id,
                    "channel_type": channel_type
                },
                use_service_key=True
            )
            return result is not None
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Unbind failed: {e}")
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
