import httpx
from typing import Optional, Any
from app.config import settings

class SupabaseAuthResponse:
    """Auth 回應包裝"""
    def __init__(self, data: dict):
        self._data = data
        self.user = SupabaseUser(data.get("user")) if data.get("user") else None
        self.session = SupabaseSession(data.get("session")) if data.get("session") else None
        self.error = data.get("error")

class SupabaseUser:
    """用戶資料包裝"""
    def __init__(self, data: dict):
        self._data = data or {}
        self.id = self._data.get("id")
        self.email = self._data.get("email")
        self.email_confirmed_at = self._data.get("email_confirmed_at")
        self.created_at = self._data.get("created_at")
        self.user_metadata = self._data.get("user_metadata", {})

class SupabaseSession:
    """Session 資料包裝"""
    def __init__(self, data: dict):
        self._data = data or {}
        self.access_token = self._data.get("access_token")
        self.refresh_token = self._data.get("refresh_token")
        self.expires_in = self._data.get("expires_in")
        self.token_type = self._data.get("token_type")

class SupabaseService:
    """Supabase 服務 - 使用 httpx 直接呼叫 API"""
    
    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.anon_key = settings.SUPABASE_ANON_KEY
        self.service_key = settings.SUPABASE_SERVICE_ROLE_KEY
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        if not self._client:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client
    
    def _headers(self, use_service_key: bool = False) -> dict:
        """取得請求標頭"""
        key = self.service_key if use_service_key else self.anon_key
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
    
    def _auth_headers(self, access_token: str) -> dict:
        """取得帶用戶 Token 的標頭"""
        return {
            "apikey": self.anon_key,
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    # ========== Auth API ==========
    
    async def sign_up(
        self, 
        email: str, 
        password: str, 
        metadata: dict = None
    ) -> SupabaseAuthResponse:
        """用戶註冊"""
        payload = {
            "email": email,
            "password": password
        }
        if metadata:
            payload["data"] = metadata
        
        response = await self.client.post(
            f"{self.url}/auth/v1/signup",
            headers=self._headers(),
            json=payload
        )
        
        data = response.json()
        
        if response.status_code >= 400:
            raise Exception(data.get("msg") or data.get("message") or "註冊失敗")
        
        return SupabaseAuthResponse(data)
    
    async def sign_in_with_password(
        self, 
        email: str, 
        password: str
    ) -> SupabaseAuthResponse:
        """密碼登入"""
        response = await self.client.post(
            f"{self.url}/auth/v1/token?grant_type=password",
            headers=self._headers(),
            json={
                "email": email,
                "password": password
            }
        )
        
        data = response.json()
        
        if response.status_code >= 400:
            error_msg = data.get("error_description") or data.get("msg") or "登入失敗"
            raise Exception(error_msg)
        
        # 包裝回應格式
        return SupabaseAuthResponse({
            "user": data.get("user"),
            "session": {
                "access_token": data.get("access_token"),
                "refresh_token": data.get("refresh_token"),
                "expires_in": data.get("expires_in"),
                "token_type": data.get("token_type")
            }
        })
    
    async def sign_out(self, access_token: str) -> bool:
        """登出"""
        response = await self.client.post(
            f"{self.url}/auth/v1/logout",
            headers=self._auth_headers(access_token)
        )
        return response.status_code < 400
    
    async def get_user(self, access_token: str) -> Optional[SupabaseUser]:
        """取得當前用戶"""
        response = await self.client.get(
            f"{self.url}/auth/v1/user",
            headers=self._auth_headers(access_token)
        )
        
        if response.status_code >= 400:
            return None
        
        return SupabaseUser(response.json())
    
    async def refresh_session(self, refresh_token: str) -> SupabaseAuthResponse:
        """刷新 Session"""
        response = await self.client.post(
            f"{self.url}/auth/v1/token?grant_type=refresh_token",
            headers=self._headers(),
            json={"refresh_token": refresh_token}
        )
        
        data = response.json()
        
        if response.status_code >= 400:
            raise Exception(data.get("error_description") or "刷新失敗")
        
        return SupabaseAuthResponse({
            "user": data.get("user"),
            "session": {
                "access_token": data.get("access_token"),
                "refresh_token": data.get("refresh_token"),
                "expires_in": data.get("expires_in")
            }
        })
    
    async def reset_password_email(
        self, 
        email: str, 
        redirect_url: str = None
    ) -> bool:
        """發送重設密碼郵件"""
        payload = {"email": email}
        if redirect_url:
            payload["redirect_to"] = redirect_url
        
        response = await self.client.post(
            f"{self.url}/auth/v1/recover",
            headers=self._headers(),
            json=payload
        )
        return response.status_code < 400
    
    # ========== Admin Auth API ==========
    
    async def admin_get_user(self, user_id: str) -> Optional[SupabaseUser]:
        """管理員取得用戶"""
        response = await self.client.get(
            f"{self.url}/auth/v1/admin/users/{user_id}",
            headers=self._headers(use_service_key=True)
        )
        
        if response.status_code >= 400:
            return None
        
        return SupabaseUser(response.json())
    
    async def admin_list_users(
        self, 
        page: int = 1, 
        per_page: int = 50
    ) -> list[SupabaseUser]:
        """管理員列出用戶"""
        response = await self.client.get(
            f"{self.url}/auth/v1/admin/users",
            headers=self._headers(use_service_key=True),
            params={"page": page, "per_page": per_page}
        )
        
        if response.status_code >= 400:
            return []
        
        data = response.json()
        users = data.get("users", []) if isinstance(data, dict) else data
        return [SupabaseUser(u) for u in users]
    
    async def admin_delete_user(self, user_id: str) -> bool:
        """管理員刪除用戶"""
        response = await self.client.delete(
            f"{self.url}/auth/v1/admin/users/{user_id}",
            headers=self._headers(use_service_key=True)
        )
        return response.status_code < 400
    
    async def admin_update_user(
        self, 
        user_id: str, 
        attributes: dict
    ) -> Optional[SupabaseUser]:
        """管理員更新用戶"""
        response = await self.client.put(
            f"{self.url}/auth/v1/admin/users/{user_id}",
            headers=self._headers(use_service_key=True),
            json=attributes
        )
        
        if response.status_code >= 400:
            return None
        
        return SupabaseUser(response.json())
    
    # ========== Database API (PostgREST) ==========
    
    async def table_select(
        self,
        table: str,
        select: str = "*",
        filters: dict = None,
        use_service_key: bool = False
    ) -> list[dict]:
        """查詢表格"""
        url = f"{self.url}/rest/v1/{table}?select={select}"
        
        headers = self._headers(use_service_key)
        
        # 添加過濾條件
        if filters:
            for key, value in filters.items():
                # 如果 value 已經包含操作符（如 eq., gt., lt.），直接使用
                # 否則預設使用 eq.
                if isinstance(value, str) and any(value.startswith(op) for op in ['eq.', 'gt.', 'lt.', 'gte.', 'lte.', 'neq.', 'like.', 'ilike.', 'is.', 'in.']):
                    url += f"&{key}={value}"
                else:
                    url += f"&{key}=eq.{value}"
        
        response = await self.client.get(url, headers=headers)
        
        if response.status_code >= 400:
            return []
        
        return response.json()
    
    async def table_insert(
        self,
        table: str,
        data: dict,
        use_service_key: bool = False
    ) -> Optional[dict]:
        """插入資料"""
        headers = self._headers(use_service_key)
        headers["Prefer"] = "return=representation"
        
        response = await self.client.post(
            f"{self.url}/rest/v1/{table}",
            headers=headers,
            json=data
        )
        
        if response.status_code >= 400:
            error = response.json()
            raise Exception(error.get("message") or "插入失敗")
        
        result = response.json()
        return result[0] if isinstance(result, list) and result else result
    
    async def table_update(
        self,
        table: str,
        data: dict,
        filters: dict,
        use_service_key: bool = False
    ) -> Optional[dict]:
        """更新資料"""
        url = f"{self.url}/rest/v1/{table}"
        
        # 添加過濾條件
        filter_parts = [f"{k}=eq.{v}" for k, v in filters.items()]
        url += "?" + "&".join(filter_parts)
        
        headers = self._headers(use_service_key)
        headers["Prefer"] = "return=representation"
        
        response = await self.client.patch(url, headers=headers, json=data)
        
        if response.status_code >= 400:
            return None
        
        result = response.json()
        return result[0] if isinstance(result, list) and result else result
    
    async def table_delete(
        self,
        table: str,
        filters: dict,
        use_service_key: bool = False
    ) -> bool:
        """刪除資料"""
        url = f"{self.url}/rest/v1/{table}"
        
        filter_parts = [f"{k}=eq.{v}" for k, v in filters.items()]
        url += "?" + "&".join(filter_parts)
        
        response = await self.client.delete(
            url, 
            headers=self._headers(use_service_key)
        )
        return response.status_code < 400
    
    # ========== 清理 ==========
    
    async def close(self):
        """關閉連線"""
        if self._client:
            await self._client.aclose()
            self._client = None

# 單例
supabase_service = SupabaseService()