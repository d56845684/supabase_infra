from datetime import date
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
    async def cleanup_created_user(
        user_id: str,
        entity_table: str | None,
        entity_id: str | None
    ) -> None:
        """註冊失敗時清理已建立的資料"""
        try:
            await supabase_service.table_delete(
                table="user_profiles",
                filters={"id": user_id},
                use_service_key=True
            )
        except Exception as cleanup_error:
            print(f"清理 user_profiles 失敗: {cleanup_error}")

        if entity_table and entity_id:
            try:
                await supabase_service.table_delete(
                    table=entity_table,
                    filters={"id": entity_id},
                    use_service_key=True
                )
            except Exception as cleanup_error:
                print(f"清理 {entity_table} 失敗: {cleanup_error}")

        try:
            await supabase_service.admin_delete_user(user_id)
        except Exception as cleanup_error:
            print(f"清理 auth.user 失敗: {cleanup_error}")

    created_user_id: str | None = None
    created_entity_table: str | None = None
    created_entity_id: str | None = None

    try:
        role = data.role.lower()
        allowed_roles = {"student", "teacher", "employee", "admin"}
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無效的角色"
            )

        result = await supabase_service.sign_up(
            email=data.email,
            password=data.password,
            metadata={"name": data.name, "role": role}
        )
        
        user = result.user
        
        if user and user.id:
            created_user_id = user.id
            try:
                if role == "student":
                    created_entity_table = "students"
                    entity_data = {
                        "student_no": f"S{user.id[:8].upper()}",
                        "name": data.name,
                        "email": data.email
                    }
                elif role == "teacher":
                    created_entity_table = "teachers"
                    entity_data = {
                        "teacher_no": f"T{user.id[:8].upper()}",
                        "name": data.name,
                        "email": data.email
                    }
                else:
                    created_entity_table = "employees"
                    entity_data = {
                        "employee_no": f"E{user.id[:8].upper()}",
                        "name": data.name,
                        "email": data.email,
                        "employee_type": "admin" if role == "admin" else "full_time",
                        "hire_date": date.today().isoformat()
                    }

                entity_result = await supabase_service.table_insert(
                    table=created_entity_table,
                    data=entity_data,
                    use_service_key=True
                )
                created_entity_id = entity_result.get("id") if entity_result else None
                if not created_entity_id:
                    raise Exception("建立對應實體失敗")
            except Exception as entity_error:
                print(f"建立 {created_entity_table} 失敗: {entity_error}")
                await cleanup_created_user(
                    user.id,
                    created_entity_table,
                    created_entity_id
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="註冊失敗，請稍後再試"
                ) from entity_error

            # 建立 user_profile 記錄
            try:
                profile_data = {
                    "id": user.id,
                    "role": role
                }
                if role == "student":
                    profile_data["student_id"] = created_entity_id
                elif role == "teacher":
                    profile_data["teacher_id"] = created_entity_id
                else:
                    profile_data["employee_id"] = created_entity_id
                
                await supabase_service.table_insert(
                    table="user_profiles",
                    data=profile_data,
                    use_service_key=True
                )
            except Exception as profile_error:
                print(f"建立 user_profile 失敗: {profile_error}")
                await cleanup_created_user(
                    user.id,
                    created_entity_table,
                    created_entity_id
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="註冊失敗，請稍後再試"
                ) from profile_error
            
            return BaseResponse(message="註冊成功，請檢查您的郵箱進行驗證")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="註冊失敗，請稍後再試"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        if created_user_id:
            await cleanup_created_user(
                created_user_id,
                created_entity_table,
                created_entity_id
            )
        error_msg = str(e)
        if "already registered" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="此郵箱已被註冊"
            ) from e
        if "invalid email" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無效的郵箱格式"
            ) from e
        if "password" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密碼不符合要求（至少6位）"
            ) from e
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"註冊失敗: {error_msg}"
        ) from e

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
