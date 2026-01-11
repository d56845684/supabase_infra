from fastapi import APIRouter, Request, Response, Depends, HTTPException, status
from app.services.auth_service import auth_service
from app.services.session_service import session_service
from app.services.supabase_service import supabase_service
from app.core.dependencies import get_current_user, CurrentUser
from app.schemas.auth import (
    LoginRequest, LoginResponse, RegisterRequest,
    LogoutRequest, RefreshResponse, PasswordResetRequest,
    UserInfo, TokenPair
)
from app.schemas.response import BaseResponse, DataResponse
from app.schemas.user import UserSessionInfo, UserSessionsResponse
from app.core.security import hash_session_id

router = APIRouter(prefix="/auth", tags=["認證"])

@router.post("/register", response_model=BaseResponse)
async def register(data: RegisterRequest):
    """用戶註冊"""
    try:
        role = data.role.lower()
        allowed_roles = {"student", "teacher", "employee"}
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="寫入失敗: 不支援的角色"
            )

        missing_fields = []
        if role == "employee":
            if not data.employee_type:
                missing_fields.append("employee_type")
            if not data.hire_date:
                missing_fields.append("hire_date")

        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"寫入失敗: 缺少必要參數 {', '.join(missing_fields)}"
            )

        result = await supabase_service.sign_up(
            email=data.email,
            password=data.password,
            metadata={"name": data.name, "role": role}
        )
        
        user = result.user
        
        if user and user.id:
            if role == "student":
                entity_payload = {
                    "name": data.name,
                    "email": data.email,
                    "phone": data.phone,
                    "address": data.address,
                    "birth_date": data.birth_date
                }
                entity_payload = {k: v for k, v in entity_payload.items() if v is not None}
                entity = await supabase_service.table_insert(
                    table="students",
                    data=entity_payload,
                    use_service_key=True
                )
                profile_data = {
                    "id": user.id,
                    "role": role,
                    "student_id": entity["id"]
                }
            elif role == "teacher":
                entity_payload = {
                    "name": data.name,
                    "email": data.email,
                    "phone": data.phone,
                    "address": data.address
                }
                entity_payload = {k: v for k, v in entity_payload.items() if v is not None}
                entity = await supabase_service.table_insert(
                    table="teachers",
                    data=entity_payload,
                    use_service_key=True
                )
                profile_data = {
                    "id": user.id,
                    "role": role,
                    "teacher_id": entity["id"]
                }
            else:
                entity_payload = {
                    "employee_type": data.employee_type,
                    "name": data.name,
                    "email": data.email,
                    "phone": data.phone,
                    "address": data.address,
                    "hire_date": data.hire_date
                }
                entity_payload = {k: v for k, v in entity_payload.items() if v is not None}
                entity = await supabase_service.table_insert(
                    table="employees",
                    data=entity_payload,
                    use_service_key=True
                )
                profile_data = {
                    "id": user.id,
                    "role": role,
                    "employee_id": entity["id"]
                }

            await supabase_service.table_insert(
                table="user_profiles",
                data=profile_data,
                use_service_key=True
            )
            
            return BaseResponse(message="註冊成功，請檢查您的郵箱進行驗證")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="註冊失敗，請稍後再試"
        )
        
    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="此郵箱已被註冊"
            )
        if "invalid email" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無效的郵箱格式"
            )
        if "password" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密碼不符合要求（至少6位）"
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"註冊失敗: {error_msg}"
        )

@router.post("/login", response_model=LoginResponse)
async def login(
    data: LoginRequest,
    request: Request,
    response: Response
):
    """用戶登入"""
    user_info, token_pair = await auth_service.login(
        email=data.email,
        password=data.password,
        request=request,
        response=response
    )
    
    return LoginResponse(
        user=user_info,
        tokens=token_pair
    )

@router.post("/logout", response_model=BaseResponse)
async def logout(
    request: Request,
    response: Response,
    data: LogoutRequest = LogoutRequest(),
    current_user: CurrentUser = Depends(get_current_user)
):
    """用戶登出"""
    await auth_service.logout(
        request=request,
        response=response,
        logout_all_devices=data.logout_all_devices
    )
    
    message = "已登出所有裝置" if data.logout_all_devices else "登出成功"
    return BaseResponse(message=message)

@router.post("/refresh", response_model=RefreshResponse)
async def refresh_tokens(
    request: Request,
    response: Response
):
    """刷新 Token"""
    token_pair = await auth_service.refresh_tokens(
        request=request,
        response=response
    )
    
    return RefreshResponse(tokens=token_pair)

@router.get("/me", response_model=DataResponse[UserInfo])
async def get_current_user_info(
    current_user: CurrentUser = Depends(get_current_user)
):
    """取得當前用戶資訊"""
    return DataResponse(
        data=UserInfo(
            id=current_user.user_id,
            email=current_user.email,
            role=current_user.role,
            email_confirmed=True
        )
    )

@router.get("/sessions", response_model=UserSessionsResponse)
async def get_user_sessions(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user)
):
    """取得用戶所有 Sessions"""
    sessions = await session_service.get_user_sessions(current_user.user_id)
    current_session_hash = hash_session_id(current_user.session_id)
    
    session_list = [
        UserSessionInfo(
            session_id=s.session_id[:16] + "...",  # 只顯示部分
            user_agent=s.user_agent,
            ip_address=s.ip_address,
            created_at=s.created_at,
            last_activity=s.last_activity,
            is_current=(s.session_id == current_session_hash)
        )
        for s in sessions
    ]
    
    return UserSessionsResponse(
        sessions=session_list,
        total=len(session_list)
    )

@router.delete("/sessions/{session_id}", response_model=BaseResponse)
async def revoke_session(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """撤銷特定 Session"""
    # 這裡的 session_id 是前端顯示的部分 ID，需要實際查找
    sessions = await session_service.get_user_sessions(current_user.user_id)
    
    for s in sessions:
        if s.session_id.startswith(session_id.replace("...", "")):
            await session_service.destroy_session(s.session_id)
            return BaseResponse(message="Session 已撤銷")
    
    return BaseResponse(success=False, message="Session 不存在")

@router.post("/password/reset", response_model=BaseResponse)
async def request_password_reset(data: PasswordResetRequest):
    """請求重設密碼"""
    try:
        await supabase_service.reset_password_email(
            email=data.email,
            redirect_url="https://your-app.com/reset-password"
        )
        return BaseResponse(message="重設密碼郵件已發送")
    except:
        # 為了安全，不透露郵箱是否存在
        return BaseResponse(message="如果該郵箱已註冊，您將收到重設密碼郵件")
