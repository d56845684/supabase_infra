from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from typing import Optional
from app.config import settings

class SupabaseService:
    def __init__(self):
        self._client: Optional[Client] = None
        self._admin_client: Optional[Client] = None
    
    @property
    def client(self) -> Client:
        """一般客戶端 (使用 anon key)"""
        if not self._client:
            self._client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY
            )
        return self._client
    
    @property
    def admin(self) -> Client:
        """管理員客戶端 (使用 service role key，繞過 RLS)"""
        if not self._admin_client:
            self._admin_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY,
                options=ClientOptions(
                    auto_refresh_token=False,
                    persist_session=False
                )
            )
        return self._admin_client
    
    # ========== Auth 操作 ==========
    
    def sign_up(self, email: str, password: str, metadata: dict = None):
        """用戶註冊"""
        options = {"data": metadata} if metadata else {}
        return self.client.auth.sign_up({
            "email": email,
            "password": password,
            "options": options
        })
    
    def sign_in_with_password(self, email: str, password: str):
        """密碼登入"""
        return self.client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
    
    def sign_in_with_oauth(self, provider: str, redirect_url: str):
        """OAuth 登入"""
        return self.client.auth.sign_in_with_oauth({
            "provider": provider,
            "options": {"redirect_to": redirect_url}
        })
    
    def sign_out(self):
        """登出"""
        return self.client.auth.sign_out()
    
    def get_user(self, jwt: str):
        """透過 JWT 取得用戶"""
        return self.client.auth.get_user(jwt)
    
    def refresh_session(self, refresh_token: str):
        """刷新 Session"""
        return self.client.auth.refresh_session(refresh_token)
    
    def reset_password_email(self, email: str, redirect_url: str):
        """發送重設密碼郵件"""
        return self.client.auth.reset_password_email(
            email,
            {"redirect_to": redirect_url}
        )
    
    def update_user(self, jwt: str, attributes: dict):
        """更新用戶資料"""
        return self.admin.auth.admin.update_user_by_id(
            jwt,
            attributes
        )
    
    # ========== 用戶管理 (Admin) ==========
    
    def admin_get_user(self, user_id: str):
        """管理員取得用戶"""
        return self.admin.auth.admin.get_user_by_id(user_id)
    
    def admin_list_users(self, page: int = 1, per_page: int = 50):
        """管理員列出用戶"""
        return self.admin.auth.admin.list_users(
            page=page,
            per_page=per_page
        )
    
    def admin_delete_user(self, user_id: str):
        """管理員刪除用戶"""
        return self.admin.auth.admin.delete_user(user_id)

# 單例
supabase_service = SupabaseService()