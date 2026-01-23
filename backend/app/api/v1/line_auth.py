"""
Line 認證 API 端點
支援多頻道（學生/老師/員工使用不同 Channel）
"""
from typing import Literal
from fastapi import APIRouter, Request, Response, Depends, HTTPException, Query

from app.config import settings, ChannelType
from app.services.line_oauth_service import line_oauth_service
from app.services.line_binding_service import line_binding_service
from app.services.auth_service import auth_service
from app.core.dependencies import get_current_user, CurrentUser
from app.schemas.line import (
    LineLoginUrlResponse,
    LineBindingStatus,
    LineBindingResponse,
    LineBindingsListResponse,
)
from app.schemas.response import BaseResponse

router = APIRouter(prefix="/auth/line", tags=["Line 認證"])


def get_channel_type_from_role(role: str) -> ChannelType:
    """根據用戶角色取得對應的頻道類型"""
    role_to_channel = {
        "student": "student",
        "teacher": "teacher",
        "employee": "employee",
        "admin": "employee",
    }
    return role_to_channel.get(role, "student")


@router.get("/login", response_model=LineLoginUrlResponse)
async def line_login(
    channel: ChannelType = Query("student", description="角色頻道類型（用於綁定後的角色識別）")
):
    """
    取得 Line 登入 URL

    導向此 URL 開始 Line OAuth 流程。
    所有角色共用同一個 Line Login Channel，但 channel 參數會記錄在 state 中，
    用於識別用戶綁定的角色類型。
    """
    if not line_oauth_service.is_configured:
        raise HTTPException(status_code=503, detail="Line 登入功能未啟用")

    state = await line_oauth_service.generate_state(channel)
    url = line_oauth_service.get_authorization_url(state, channel)

    return LineLoginUrlResponse(url=url, state=state, channel_type=channel)


@router.get("/callback")
async def line_callback(
    request: Request,
    response: Response,
    code: str = None,
    state: str = None,
    error: str = None,
    error_description: str = None,
):
    """
    Line OAuth 回調

    處理 Line 授權後的回調，自動登入或建立帳號。
    角色類型（channel_type）從 state 中取得。
    """
    from fastapi.responses import RedirectResponse
    import logging
    logger = logging.getLogger(__name__)

    # 記錄收到的參數
    logger.info(f"Line callback received - code: {code[:10] if code else 'None'}..., state: {state[:10] if state else 'None'}..., error: {error}")

    # 處理錯誤
    if error:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/error?error={error}&description={error_description or ''}"
        )

    # 檢查必要參數
    if not code or not state:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/error?error=missing_params&description=code_or_state_missing"
        )

    # 驗證 state
    is_valid, existing_user_id, state_channel = await line_oauth_service.validate_state(state)
    if not is_valid:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/error?error=invalid_state"
        )

    # 使用 state 中的 channel_type
    channel_type = state_channel or "student"

    try:
        # 交換 tokens
        tokens = await line_oauth_service.exchange_code_for_tokens(code, channel_type)

        # 取得用戶資料
        profile, email = await line_oauth_service.get_user_profile_data(tokens)

        # 檢查是否已有綁定
        existing_binding = await line_binding_service.get_binding_by_line_id(
            profile.user_id, channel_type
        )

        if existing_binding:
            # 已綁定，直接登入
            user_id = existing_binding.user_id
            is_new_user = False
        elif existing_user_id:
            # 綁定到現有帳號（從 state 取得）
            await line_binding_service.create_binding(
                existing_user_id, profile, channel_type
            )
            user_id = existing_user_id
            is_new_user = False
        elif email:
            # 檢查 email 是否已存在
            existing_user = await line_oauth_service.find_user_by_email(email)
            if existing_user:
                # 自動合併帳號
                user_id = existing_user["id"]
                await line_binding_service.create_binding(
                    user_id, profile, channel_type
                )
                is_new_user = False
            else:
                # 建立新帳號
                result = await line_oauth_service.create_user_from_line(
                    profile, channel_type, email
                )
                user_id = result.user.id
                await line_binding_service.create_binding(
                    user_id, profile, channel_type
                )
                is_new_user = True
        else:
            # 沒有 email，建立新帳號
            result = await line_oauth_service.create_user_from_line(
                profile, channel_type
            )
            user_id = result.user.id
            await line_binding_service.create_binding(
                user_id, profile, channel_type
            )
            is_new_user = True

        # 執行登入流程（設定 cookies）
        await auth_service.login_by_user_id(user_id, request, response)

        # 導向前端
        redirect_url = f"{settings.FRONTEND_URL}/auth/success?new_user={is_new_user}&channel={channel_type}"
        return RedirectResponse(url=redirect_url, status_code=302)

    except Exception as e:
        import urllib.parse
        error_msg = urllib.parse.quote(str(e))
        logger.error(f"Line auth failed: {e}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/error?error=line_auth_failed&description={error_msg}"
        )


@router.post("/bind", response_model=LineBindingResponse)
async def bind_line(
    channel: ChannelType = Query(None, description="頻道類型（預設根據角色決定）"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    取得綁定 Line 的 URL

    已登入用戶用此端點開始綁定 Line 流程
    """
    # 如果未指定頻道，根據用戶角色決定
    channel_type = channel or get_channel_type_from_role(current_user.role)

    if not line_oauth_service.is_channel_configured(channel_type):
        raise HTTPException(status_code=503, detail=f"Line {channel_type} 頻道功能未啟用")

    # 檢查是否已綁定
    existing = await line_binding_service.get_binding_by_user(
        current_user.user_id, channel_type
    )
    if existing and existing.binding_status == "active":
        return LineBindingResponse(
            success=False,
            message=f"已綁定 Line {channel_type} 頻道帳號",
            data=LineBindingStatus(
                is_bound=True,
                channel_type=channel_type,
                line_display_name=existing.line_display_name,
                line_picture_url=existing.line_picture_url,
                bound_at=existing.bound_at,
            )
        )

    # 生成含用戶 ID 的 state
    state = await line_oauth_service.generate_state(channel_type, current_user.user_id)
    url = line_oauth_service.get_authorization_url(state, channel_type)

    return LineBindingResponse(
        success=True,
        message="請前往以下 URL 綁定 Line",
        data=LineBindingStatus(
            is_bound=False,
            channel_type=channel_type,
            bind_url=url,
        )
    )


@router.delete("/unbind", response_model=BaseResponse)
async def unbind_line(
    channel: ChannelType = Query(None, description="頻道類型（預設根據角色決定）"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    解除 Line 綁定
    """
    # 如果未指定頻道，根據用戶角色決定
    channel_type = channel or get_channel_type_from_role(current_user.role)

    success = await line_binding_service.unbind(current_user.user_id, channel_type)

    if success:
        return BaseResponse(message=f"已解除 Line {channel_type} 頻道綁定")
    else:
        return BaseResponse(success=False, message="解除綁定失敗")


@router.get("/status", response_model=LineBindingResponse)
async def get_line_status(
    channel: ChannelType = Query(None, description="頻道類型（預設根據角色決定）"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    取得 Line 綁定狀態
    """
    # 如果未指定頻道，根據用戶角色決定
    channel_type = channel or get_channel_type_from_role(current_user.role)

    binding = await line_binding_service.get_binding_by_user(
        current_user.user_id, channel_type
    )

    if binding and binding.binding_status == "active":
        return LineBindingResponse(
            success=True,
            message="已綁定 Line",
            data=LineBindingStatus(
                is_bound=True,
                channel_type=channel_type,
                line_display_name=binding.line_display_name,
                line_picture_url=binding.line_picture_url,
                bound_at=binding.bound_at,
            )
        )
    else:
        return LineBindingResponse(
            success=True,
            message="尚未綁定 Line",
            data=LineBindingStatus(
                is_bound=False,
                channel_type=channel_type
            )
        )


@router.get("/bindings", response_model=LineBindingsListResponse)
async def get_all_line_bindings(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    取得用戶所有頻道的 Line 綁定狀態
    """
    bindings = await line_binding_service.get_all_bindings_by_user(current_user.user_id)

    binding_list = [
        LineBindingStatus(
            is_bound=b.binding_status == "active",
            channel_type=b.channel_type,
            line_display_name=b.line_display_name,
            line_picture_url=b.line_picture_url,
            bound_at=b.bound_at,
        )
        for b in bindings
    ]

    return LineBindingsListResponse(
        success=True,
        message=f"共有 {len(binding_list)} 個頻道綁定",
        bindings=binding_list
    )
