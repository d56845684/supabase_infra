from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal

# 員工類型定義
EmployeeType = Literal["admin", "full_time", "part_time", "intern"]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "student"  # student, teacher, employee
    employee_type: Optional[EmployeeType] = Field(
        None,
        description="員工類型（僅 role 為 employee 時需要）"
    )


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
    employee_type: Optional[str] = Field(
        None,
        description="員工類型（若為員工身份）"
    )
    permission_level: int = Field(
        0,
        description="權限等級"
    )

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