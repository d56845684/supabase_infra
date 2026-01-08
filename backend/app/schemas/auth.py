from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "student"  # student, teacher

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class UserInfo(BaseModel):
    id: str
    email: str
    role: str
    email_confirmed: bool = False
    created_at: Optional[str] = None

class LoginResponse(BaseModel):
    success: bool = True
    message: str = "登入成功"
    user: UserInfo
    tokens: TokenPair

class LogoutRequest(BaseModel):
    logout_all_devices: bool = False

class RefreshResponse(BaseModel):
    success: bool = True
    tokens: TokenPair

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordUpdateRequest(BaseModel):
    current_password: str
    new_password: str