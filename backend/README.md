# FastAPI Supabase Backend

This backend authenticates against Supabase Auth and stores the access token in an HttpOnly cookie,
then proxies Supabase REST requests using that JWT so RLS remains enforced.

## Environment

- `SUPABASE_URL` (default: `http://localhost:8000`)
- `SUPABASE_ANON_KEY` (required)
- `SUPABASE_COOKIE_NAME` (default: `sb-access-token`)
- `SUPABASE_COOKIE_SECURE` (`true` to mark the cookie as secure)
- `CORS_ALLOW_ORIGINS` (comma-separated list, default `*`)
- `SUPABASE_SESSION_TABLE` (optional table name for authentication persistence)

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

## Swagger / OpenAPI

Start the server and open:

- Swagger UI: `http://localhost:8001/docs`
- OpenAPI JSON: `http://localhost:8001/openapi.json`

## Authentication Persistence (Table-backed)

If you want login sessions tracked in Postgres, set `SUPABASE_SESSION_TABLE` to a table name.
The backend will create a session row on login, validate that session (including expiry) on each
REST proxy request, and delete sessions on logout or explicit revocation. Ensure RLS allows the
user to insert/update/read/delete their own rows.

Session management endpoints:

- `GET /auth/sessions` lists active sessions (for "kick device" UI).
- `DELETE /auth/sessions/{session_id}` revokes a specific session (kicks a device).

Example schema:

```sql
create table public.auth_sessions (
  session_id uuid primary key,
  user_id uuid not null references auth.users(id),
  token_hash text not null,
  expires_at timestamptz,
  last_login_at timestamptz not null default now()
);

create unique index auth_sessions_token_hash_idx on public.auth_sessions (token_hash);

alter table public.auth_sessions enable row level security;

create policy "Users can manage their sessions"
  on public.auth_sessions
  for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);
```
