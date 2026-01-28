from pydantic_settings import BaseSettings
from pydantic import BaseModel
from functools import lru_cache
from typing import Optional, Dict, Literal

# 頻道類型
ChannelType = Literal["student", "teacher", "employee"]


class LineChannelConfig(BaseModel):
    """單一 Line Channel 設定"""
    channel_id: str = ""
    channel_secret: str = ""
    callback_url: str = ""
    messaging_token: str = ""

    @property
    def is_configured(self) -> bool:
        """檢查此頻道是否已設定"""
        return bool(self.channel_id and self.channel_secret)

    @property
    def messaging_enabled(self) -> bool:
        """檢查 Messaging API 是否已設定"""
        return bool(self.messaging_token)


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Education Management System"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str

    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None

    # Cookie
    COOKIE_DOMAIN: str = "localhost"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    COOKIE_HTTPONLY: bool = True

    # Session & Token
    SESSION_EXPIRE_MINUTES: int = 1440  # 24 hours
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ============================================
    # Line Login（登入認證）- 所有角色共用同一個 Channel
    # ============================================
    LINE_LOGIN_CHANNEL_ID: str = ""
    LINE_LOGIN_CHANNEL_SECRET: str = ""
    LINE_LOGIN_CALLBACK_URL: str = "http://localhost:8001/api/v1/auth/line/callback"

    # ============================================
    # Line Messaging（發送通知）- 每個角色使用不同的 Channel
    # ============================================
    # 學生頻道
    LINE_STUDENT_MESSAGING_TOKEN: str = ""

    # 老師頻道
    LINE_TEACHER_MESSAGING_TOKEN: str = ""

    # 員工頻道
    LINE_EMPLOYEE_MESSAGING_TOKEN: str = ""

    # Frontend URL (for OAuth redirects)
    FRONTEND_URL: str = "http://localhost:4173"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def line_login_config(self) -> LineChannelConfig:
        """取得 Line Login Channel 設定（所有角色共用）"""
        return LineChannelConfig(
            channel_id=self.LINE_LOGIN_CHANNEL_ID,
            channel_secret=self.LINE_LOGIN_CHANNEL_SECRET,
            callback_url=self.LINE_LOGIN_CALLBACK_URL,
            messaging_token="",  # Login channel 不用於發送訊息
        )

    def get_messaging_token(self, channel_type: ChannelType) -> str:
        """根據角色取得對應的 Messaging Token"""
        tokens = {
            "student": self.LINE_STUDENT_MESSAGING_TOKEN,
            "teacher": self.LINE_TEACHER_MESSAGING_TOKEN,
            "employee": self.LINE_EMPLOYEE_MESSAGING_TOKEN,
        }
        return tokens.get(channel_type, "")

    def get_line_channel(self, channel_type: ChannelType) -> LineChannelConfig:
        """根據角色取得對應的 Line Channel 設定（向後相容）"""
        # Login 使用共用的 channel，Messaging 使用各自的 token
        return LineChannelConfig(
            channel_id=self.LINE_LOGIN_CHANNEL_ID,
            channel_secret=self.LINE_LOGIN_CHANNEL_SECRET,
            callback_url=self.LINE_LOGIN_CALLBACK_URL,
            messaging_token=self.get_messaging_token(channel_type),
        )

    def get_line_channel_by_role(self, role: str) -> LineChannelConfig:
        """根據用戶角色取得對應的 Line Channel 設定"""
        role_to_channel: Dict[str, ChannelType] = {
            "student": "student",
            "teacher": "teacher",
            "employee": "employee",
            "admin": "employee",  # admin 使用員工頻道
        }
        channel_type = role_to_channel.get(role, "student")
        return self.get_line_channel(channel_type)

    @property
    def line_login_enabled(self) -> bool:
        """檢查 Line Login 是否已設定"""
        return self.line_login_config.is_configured

    @property
    def line_enabled(self) -> bool:
        """檢查是否有 Line 功能已設定（向後相容）"""
        return self.line_login_enabled

    @property
    def line_messaging_enabled(self) -> bool:
        """檢查是否有任何 Line Messaging API 已設定"""
        return any([
            bool(self.LINE_STUDENT_MESSAGING_TOKEN),
            bool(self.LINE_TEACHER_MESSAGING_TOKEN),
            bool(self.LINE_EMPLOYEE_MESSAGING_TOKEN),
        ])

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()