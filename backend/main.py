import hashlib
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Mapping

import httpx
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from models import LoginRequest

SUPABASE_URL = os.getenv("SUPABASE_URL", "http://localhost:8000")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
COOKIE_NAME = os.getenv("SUPABASE_COOKIE_NAME", "sb-access-token")
COOKIE_SECURE = os.getenv("SUPABASE_COOKIE_SECURE", "false").lower() == "true"
SESSION_TABLE = os.getenv("SUPABASE_SESSION_TABLE", "")

app = FastAPI(title="Supabase FastAPI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def build_supabase_headers(
    extra_headers: Mapping[str, str] | None = None,
) -> dict[str, str]:
    if not SUPABASE_ANON_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_ANON_KEY is not configured",
        )

    headers = {"apikey": SUPABASE_ANON_KEY}
    if extra_headers:
        headers.update(extra_headers)
    return headers


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


async def persist_session(
    access_token: str,
    user_id: str,
    expires_in: int | None,
) -> str | None:
    if not SESSION_TABLE:
        return None

    url = f"{SUPABASE_URL}/rest/v1/{SESSION_TABLE}"
    session_id = str(uuid.uuid4())
    expires_at = None
    if expires_in:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    payload = {
        "session_id": session_id,
        "user_id": user_id,
        "token_hash": hash_token(access_token),
        "expires_at": expires_at.isoformat() if expires_at else None,
        "last_login_at": datetime.now(timezone.utc).isoformat(),
    }

    headers = build_supabase_headers(
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "Prefer": "resolution=merge-duplicates",
        }
    )

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, json=payload, headers=headers)

    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Failed to persist session",
                "error": response.text,
            },
        )

    return session_id


async def delete_session_by_token(access_token: str) -> None:
    if not SESSION_TABLE:
        return

    url = f"{SUPABASE_URL}/rest/v1/{SESSION_TABLE}"
    headers = build_supabase_headers({"Authorization": f"Bearer {access_token}"})
    params = {"token_hash": f"eq.{hash_token(access_token)}"}

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.delete(url, params=params, headers=headers)

    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session",
        )


async def delete_session_by_id(access_token: str, session_id: str) -> None:
    if not SESSION_TABLE:
        return

    url = f"{SUPABASE_URL}/rest/v1/{SESSION_TABLE}"
    headers = build_supabase_headers({"Authorization": f"Bearer {access_token}"})
    params = {"session_id": f"eq.{session_id}"}

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.delete(url, params=params, headers=headers)

    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session",
        )


async def validate_session(access_token: str) -> None:
    if not SESSION_TABLE:
        return

    token_hash = hash_token(access_token)
    url = f"{SUPABASE_URL}/rest/v1/{SESSION_TABLE}"
    headers = build_supabase_headers(
        {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
    )
    params = {
        "token_hash": f"eq.{token_hash}",
        "select": "expires_at",
        "limit": "1",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url, params=params, headers=headers)

    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        )

    data = response.json()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found",
        )

    expires_at = parse_datetime(data[0].get("expires_at"))
    if expires_at and expires_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
        )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/login")
async def login(payload: LoginRequest, response: Response) -> dict[str, object]:
    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    async with httpx.AsyncClient(timeout=15) as client:
        auth_response = await client.post(
            url,
            json={"email": payload.email, "password": payload.password},
            headers=build_supabase_headers({"Content-Type": "application/json"}),
        )

    if auth_response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=auth_response.json(),
        )

    data = auth_response.json()
    access_token = data.get("access_token")
    expires_in = data.get("expires_in")
    user = data.get("user") or {}

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase did not return an access token",
        )

    user_id = user.get("id")
    session_id = None
    if user_id:
        session_id = await persist_session(access_token, user_id, expires_in)

    response.set_cookie(
        COOKIE_NAME,
        access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=expires_in,
    )

    return {"user": user, "expires_in": expires_in, "session_id": session_id}


@app.post("/auth/logout")
async def logout(request: Request, response: Response) -> dict[str, str]:
    token = request.cookies.get(COOKIE_NAME)
    if token:
        await delete_session_by_token(token)
    response.delete_cookie(COOKIE_NAME)
    return {"status": "logged_out"}


@app.get("/auth/sessions")
async def list_sessions(request: Request) -> list[dict[str, object]]:
    if not SESSION_TABLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session table is not configured",
        )
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing auth cookie",
        )

    await validate_session(token)

    url = f"{SUPABASE_URL}/rest/v1/{SESSION_TABLE}"
    headers = build_supabase_headers({"Authorization": f"Bearer {token}"})
    params = {
        "select": "session_id,last_login_at,expires_at",
        "order": "last_login_at.desc",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url, params=params, headers=headers)

    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list sessions",
        )

    return response.json()


@app.delete("/auth/sessions/{session_id}")
async def revoke_session(session_id: str, request: Request) -> dict[str, str]:
    if not SESSION_TABLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session table is not configured",
        )
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing auth cookie",
        )

    await validate_session(token)
    await delete_session_by_id(token, session_id)

    return {"status": "revoked"}


def extract_forward_headers(headers: Mapping[str, str]) -> dict[str, str]:
    allowlist = {
        "accept",
        "accept-profile",
        "content-profile",
        "content-type",
        "if-match",
        "if-none-match",
        "prefer",
        "range",
    }
    return {key: value for key, value in headers.items() if key.lower() in allowlist}


@app.api_route(
    "/rest/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def proxy_rest(path: str, request: Request) -> Response:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing auth cookie",
        )

    await validate_session(token)

    url = f"{SUPABASE_URL}/rest/v1/{path}"
    params = dict(request.query_params)
    body = await request.body()
    forward_headers = extract_forward_headers(request.headers)
    forward_headers.update(build_supabase_headers())
    forward_headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(timeout=30) as client:
        supabase_response = await client.request(
            request.method,
            url,
            params=params,
            content=body if body else None,
            headers=forward_headers,
        )

    return Response(
        content=supabase_response.content,
        status_code=supabase_response.status_code,
        media_type=supabase_response.headers.get("content-type"),
    )
