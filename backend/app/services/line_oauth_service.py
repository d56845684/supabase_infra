"""
Line OAuth 服務 - 處理 Line Login 認證流程
支援多頻道（學生/老師/員工使用不同 Channel）
"""
import secrets
import hashlib
import base64
from typing import Optional, Tuple, Literal
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from app.config import settings, LineChannelConfig, ChannelType
from app.services.redis_service import redis_service
from app.services.supabase_service import supabase_service


@dataclass
class LineTokens:
    """Line OAuth Tokens"""
    access_token: str
    token_type: str
    refresh_token: Optional[str]
    expires_in: int
    id_token: Optional[str]
    scope: str


@dataclass
class LineProfile:
    """Line 用戶資料"""
    user_id: str
    display_name: str
    picture_url: Optional[str]
    status_message: Optional[str]
    email: Optional[str] = None


class LineOAuthService:
    """Line OAuth 認證服務（多頻道支援）"""

    # Line API 端點
    AUTH_URL = "https://access.line.me/oauth2/v2.1/authorize"
    TOKEN_URL = "https://api.line.me/oauth2/v2.1/token"
    PROFILE_URL = "https://api.line.me/v2/profile"
    VERIFY_URL = "https://api.line.me/oauth2/v2.1/verify"
    REVOKE_URL = "https://api.line.me/oauth2/v2.1/revoke"

    # State 快取過期時間（秒）
    STATE_TTL = 600  # 10 分鐘

    def get_channel(self, channel_type: ChannelType) -> LineChannelConfig:
        """取得指定類型的頻道設定"""
        return settings.get_line_channel(channel_type)

    def is_channel_configured(self, channel_type: ChannelType) -> bool:
        """檢查指定頻道是否已設定"""
        return self.get_channel(channel_type).is_configured

    @property
    def is_configured(self) -> bool:
        """檢查是否有任何 Line OAuth 頻道已設定"""
        return settings.line_enabled

    async def generate_state(
        self,
        channel_type: ChannelType,
        user_id: Optional[str] = None
    ) -> str:
        """
        生成並儲存 OAuth state

        Args:
            channel_type: 頻道類型
            user_id: 如果是綁定現有帳號，傳入用戶 ID

        Returns:
            state 字串
        """
        state = secrets.token_urlsafe(32)
        state_data = {
            "channel_type": channel_type,
            "user_id": user_id
        }

        await redis_service.set_json(
            f"line_oauth_state:{state}",
            state_data,
            ex=self.STATE_TTL
        )

        return state

    async def validate_state(self, state: str) -> Tuple[bool, Optional[str], Optional[ChannelType]]:
        """
        驗證 OAuth state

        Args:
            state: state 字串

        Returns:
            (是否有效, 關聯的 user_id, 頻道類型)
        """
        state_data = await redis_service.get_json(f"line_oauth_state:{state}")
        if state_data is None:
            return False, None, None

        # 刪除已使用的 state
        await redis_service.delete(f"line_oauth_state:{state}")

        return True, state_data.get("user_id"), state_data.get("channel_type")

    def get_authorization_url(
        self,
        state: str,
        channel_type: ChannelType,
        scope: str = "profile openid email"
    ) -> str:
        """
        取得 Line OAuth 授權 URL

        Args:
            state: OAuth state
            channel_type: 頻道類型
            scope: 請求的權限範圍

        Returns:
            完整的授權 URL
        """
        channel = self.get_channel(channel_type)
        params = {
            "response_type": "code",
            "client_id": channel.channel_id,
            "redirect_uri": channel.callback_url,
            "state": state,
            "scope": scope,
        }

        return f"{self.AUTH_URL}?{urlencode(params)}"

    async def exchange_code_for_tokens(
        self,
        code: str,
        channel_type: ChannelType
    ) -> LineTokens:
        """
        用授權碼交換 Tokens

        Args:
            code: 授權碼
            channel_type: 頻道類型

        Returns:
            LineTokens 物件

        Raises:
            Exception: 如果交換失敗
        """
        channel = self.get_channel(channel_type)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": channel.callback_url,
                    "client_id": channel.channel_id,
                    "client_secret": channel.channel_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if response.status_code != 200:
                error_data = response.json()
                raise Exception(f"Line token exchange failed: {error_data}")

            data = response.json()
            return LineTokens(
                access_token=data["access_token"],
                token_type=data.get("token_type", "Bearer"),
                refresh_token=data.get("refresh_token"),
                expires_in=data.get("expires_in", 0),
                id_token=data.get("id_token"),
                scope=data.get("scope", ""),
            )

    async def get_user_profile(self, access_token: str) -> LineProfile:
        """
        取得 Line 用戶資料

        Args:
            access_token: Line access token

        Returns:
            LineProfile 物件

        Raises:
            Exception: 如果取得失敗
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.PROFILE_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if response.status_code != 200:
                raise Exception(f"Failed to get Line profile: {response.text}")

            data = response.json()
            return LineProfile(
                user_id=data["userId"],
                display_name=data["displayName"],
                picture_url=data.get("pictureUrl"),
                status_message=data.get("statusMessage"),
            )

    def decode_id_token(self, id_token: str) -> dict:
        """
        解碼 Line ID Token 取得 email

        Args:
            id_token: Line ID token

        Returns:
            解碼後的 payload
        """
        try:
            parts = id_token.split(".")
            if len(parts) != 3:
                return {}

            # 解碼 payload
            payload = parts[1]
            # 補齊 padding
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += "=" * padding

            import json
            decoded = base64.urlsafe_b64decode(payload)
            return json.loads(decoded)
        except Exception:
            return {}

    async def get_user_email(self, id_token: str) -> Optional[str]:
        """
        從 ID Token 取得用戶 email

        Args:
            id_token: Line ID token

        Returns:
            用戶 email，如果沒有則返回 None
        """
        payload = self.decode_id_token(id_token)
        return payload.get("email")

    async def verify_access_token(self, access_token: str) -> bool:
        """
        驗證 access token 是否有效

        Args:
            access_token: Line access token

        Returns:
            True 如果有效
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.VERIFY_URL,
                params={"access_token": access_token}
            )
            return response.status_code == 200

    async def revoke_token(
        self,
        access_token: str,
        channel_type: ChannelType
    ) -> bool:
        """
        撤銷 access token

        Args:
            access_token: Line access token
            channel_type: 頻道類型

        Returns:
            True 如果成功
        """
        channel = self.get_channel(channel_type)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.REVOKE_URL,
                data={
                    "access_token": access_token,
                    "client_id": channel.channel_id,
                    "client_secret": channel.channel_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            return response.status_code == 200

    async def find_user_by_email(self, email: str) -> Optional[dict]:
        """
        透過 email 查找現有用戶

        Args:
            email: 用戶 email

        Returns:
            用戶資料，如果不存在則返回 None
        """
        try:
            users = await supabase_service.admin_list_users()
            for user in users:
                if user.get("email") == email:
                    return user
            return None
        except Exception:
            return None

    async def find_user_by_line_id(
        self,
        line_user_id: str,
        channel_type: ChannelType
    ) -> Optional[dict]:
        """
        透過 Line User ID 查找已綁定的用戶

        Args:
            line_user_id: Line 用戶 ID
            channel_type: 頻道類型

        Returns:
            用戶資料，如果不存在則返回 None
        """
        try:
            result = await supabase_service.table_select(
                table="line_user_bindings",
                select="user_id",
                filters={
                    "line_user_id": f"eq.{line_user_id}",
                    "channel_type": f"eq.{channel_type}",
                    "binding_status": "eq.active"
                },
                use_service_key=True
            )

            if result and len(result) > 0:
                user_id = result[0]["user_id"]
                return await supabase_service.admin_get_user(user_id)

            return None
        except Exception:
            return None

    async def create_user_from_line(
        self,
        profile: LineProfile,
        channel_type: ChannelType,
        email: Optional[str] = None
    ) -> dict:
        """
        從 Line 資料建立新用戶

        Args:
            profile: Line 用戶資料
            channel_type: 頻道類型
            email: 用戶 email（如果有）

        Returns:
            新建立的用戶資料
        """
        # 如果沒有 email，生成一個佔位 email
        if not email:
            email = f"line_{profile.user_id}@line.placeholder"

        # 生成隨機密碼
        random_password = secrets.token_urlsafe(32)

        # 根據頻道類型決定預設角色
        role_map = {
            "student": "student",
            "teacher": "teacher",
            "employee": "employee",
        }
        default_role = role_map.get(channel_type, "student")

        # 透過 Supabase 建立用戶
        result = await supabase_service.sign_up(
            email=email,
            password=random_password,
            metadata={
                "name": profile.display_name,
                "role": default_role,
                "avatar_url": profile.picture_url,
                "line_user_id": profile.user_id,
            }
        )

        return result

    async def get_user_profile_data(
        self,
        tokens: LineTokens
    ) -> Tuple[LineProfile, Optional[str]]:
        """
        取得完整的用戶資料（包含 email）

        Args:
            tokens: Line tokens

        Returns:
            (LineProfile, email)
        """
        profile = await self.get_user_profile(tokens.access_token)

        email = None
        if tokens.id_token:
            email = await self.get_user_email(tokens.id_token)

        profile.email = email
        return profile, email


# 單例
line_oauth_service = LineOAuthService()
