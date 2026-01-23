#!/usr/bin/env python3
"""
Live Authentication Test Script

測試真實運行中的認證服務，支援多角色測試及清理測試資料。

使用方式:
    # 執行所有角色測試
    python tests/live_auth_test.py

    # 測試特定角色
    python tests/live_auth_test.py --roles student teacher

    # 只清理測試資料
    python tests/live_auth_test.py --cleanup-only

    # 執行測試但不清理
    python tests/live_auth_test.py --no-cleanup
"""

import httpx
import asyncio
import argparse
import sys
import os
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

# 設定 (使用 127.0.0.1 避免 IPv6 問題)
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8001")
SUPABASE_URL = os.getenv("SUPABASE_URL", "http://127.0.0.1:8000")
SERVICE_ROLE_KEY = os.getenv("SERVICE_ROLE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UiLCJpYXQiOjE3NjczMjM3NDcsImV4cCI6MTkyNTAwMzc0N30.h8XFj9oZdc0ZaiczkL83AkQtf6zKDTrdTO3SxtrZVU8")

# 測試用戶前綴（方便識別和清理）
TEST_EMAIL_PREFIX = "test_auth_"
TEST_EMAIL_DOMAIN = "@example.com"

# 支援的角色列表
SUPPORTED_ROLES = ["student", "teacher", "employee"]


@dataclass
class TestResult:
    name: str
    passed: bool
    role: str = ""
    message: str = ""
    duration_ms: float = 0


@dataclass
class TestContext:
    """測試上下文，儲存測試過程中的資料"""
    test_email: str = ""
    test_password: str = "TestPassword123!"
    test_name: str = "Test User"
    test_role: str = "student"
    user_id: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    session_id: Optional[str] = None
    cookies: dict = field(default_factory=dict)


class LiveAuthTester:
    def __init__(self, backend_url: str, supabase_url: str, service_role_key: str, roles: list[str]):
        self.backend_url = backend_url.rstrip("/")
        self.supabase_url = supabase_url.rstrip("/")
        self.service_role_key = service_role_key
        self.roles = roles
        self.results: list[TestResult] = []
        self.created_user_ids: list[str] = []

        # httpx client config
        self.client_kwargs = {
            "follow_redirects": True,
            "timeout": httpx.Timeout(30.0, connect=10.0)
        }

    def _create_context(self, role: str) -> TestContext:
        """為特定角色建立測試上下文"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return TestContext(
            test_email=f"{TEST_EMAIL_PREFIX}{role}_{timestamp}{TEST_EMAIL_DOMAIN}",
            test_name=f"Test {role.capitalize()}",
            test_role=role
        )

    async def run_all_tests(self) -> bool:
        """執行所有角色的測試"""
        print(f"\n{'='*60}")
        print(f"🧪 Live Authentication Tests (Multi-Role)")
        print(f"{'='*60}")
        print(f"Backend URL: {self.backend_url}")
        print(f"Roles to test: {', '.join(self.roles)}")
        print(f"{'='*60}\n")

        all_passed = True

        for role in self.roles:
            role_passed = await self._run_role_tests(role)
            if not role_passed:
                all_passed = False

        self._print_final_summary()
        return all_passed

    async def _run_role_tests(self, role: str) -> bool:
        """執行特定角色的所有測試"""
        print(f"\n{'─'*60}")
        print(f"👤 Testing Role: {role.upper()}")
        print(f"{'─'*60}")

        ctx = self._create_context(role)
        print(f"Test Email: {ctx.test_email}\n")

        tests = [
            ("Health Check", self._test_health_check),
            ("User Registration", self._test_register),
            ("User Login", self._test_login),
            ("Get Current User", self._test_get_me),
            ("Verify Role", self._test_verify_role),
            ("Get Sessions", self._test_get_sessions),
            ("Token Refresh", self._test_refresh_token),
            ("Logout", self._test_logout),
            ("Access After Logout", self._test_access_after_logout),
        ]

        role_results = []
        for name, test_fn in tests:
            result = await self._run_single_test(name, test_fn, ctx, role)
            role_results.append(result)
            self.results.append(result)

        # 記錄建立的用戶 ID
        if ctx.user_id:
            self.created_user_ids.append(ctx.user_id)

        passed = sum(1 for r in role_results if r.passed)
        failed = sum(1 for r in role_results if not r.passed)
        print(f"\n📋 Role '{role}': {passed} passed, {failed} failed")

        return failed == 0

    async def _run_single_test(self, name: str, test_fn, ctx: TestContext, role: str) -> TestResult:
        """執行單個測試"""
        print(f"  ▶ {name}...", end=" ", flush=True)
        start = datetime.now()

        try:
            await test_fn(ctx)
            duration = (datetime.now() - start).total_seconds() * 1000
            print(f"✅ ({duration:.0f}ms)")
            return TestResult(name, True, role, "OK", duration)
        except AssertionError as e:
            duration = (datetime.now() - start).total_seconds() * 1000
            print(f"❌ {e}")
            return TestResult(name, False, role, str(e), duration)
        except Exception as e:
            duration = (datetime.now() - start).total_seconds() * 1000
            print(f"❌ Error: {e}")
            return TestResult(name, False, role, f"Error: {e}", duration)

    def _print_final_summary(self):
        """列印最終測試摘要"""
        print(f"\n{'='*60}")
        print("📊 Final Test Summary")
        print(f"{'='*60}")

        # 按角色分組
        for role in self.roles:
            role_results = [r for r in self.results if r.role == role]
            passed = sum(1 for r in role_results if r.passed)
            failed = sum(1 for r in role_results if not r.passed)
            status = "✅" if failed == 0 else "❌"
            print(f"\n  {status} {role.upper()}: {passed} passed, {failed} failed")

            for r in role_results:
                status = "✅" if r.passed else "❌"
                print(f"      {status} {r.name}: {r.message} ({r.duration_ms:.0f}ms)")

        total_passed = sum(1 for r in self.results if r.passed)
        total_failed = sum(1 for r in self.results if not r.passed)
        total_time = sum(r.duration_ms for r in self.results)

        print(f"\n{'='*60}")
        print(f"Total: {total_passed} passed, {total_failed} failed ({total_time:.0f}ms)")
        print(f"{'='*60}\n")

    # ========== 測試案例 ==========

    async def _test_health_check(self, ctx: TestContext):
        """測試健康檢查端點"""
        async with httpx.AsyncClient(**self.client_kwargs) as client:
            resp = await client.get(f"{self.backend_url}/api/v1/health")
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"

    async def _test_register(self, ctx: TestContext):
        """測試用戶註冊"""
        async with httpx.AsyncClient(**self.client_kwargs) as client:
            # 建立註冊資料
            register_data = {
                "email": ctx.test_email,
                "password": ctx.test_password,
                "name": ctx.test_name,
                "role": ctx.test_role
            }

            # 如果是 employee 角色，需要指定 employee_type
            if ctx.test_role == "employee":
                register_data["employee_type"] = "intern"  # 預設為工讀生

            resp = await client.post(
                f"{self.backend_url}/api/v1/auth/register",
                json=register_data
            )

            data = resp.json()
            if resp.status_code == 200 and data.get("success"):
                return
            elif "already registered" in data.get("message", "").lower():
                return
            else:
                assert False, f"Registration failed: {data}"

    async def _test_login(self, ctx: TestContext):
        """測試用戶登入"""
        async with httpx.AsyncClient(**self.client_kwargs) as client:
            resp = await client.post(
                f"{self.backend_url}/api/v1/auth/login",
                json={
                    "email": ctx.test_email,
                    "password": ctx.test_password
                }
            )

            assert resp.status_code == 200, f"Login failed: {resp.text}"
            data = resp.json()
            assert data.get("success"), f"Login not successful: {data}"

            ctx.cookies = dict(resp.cookies)

            if "tokens" in data:
                ctx.access_token = data["tokens"].get("access_token")
                ctx.refresh_token = data["tokens"].get("refresh_token")

            if "user" in data:
                ctx.user_id = data["user"].get("id")

    async def _test_get_me(self, ctx: TestContext):
        """測試取得當前用戶資訊"""
        async with httpx.AsyncClient(cookies=ctx.cookies, **self.client_kwargs) as client:
            resp = await client.get(f"{self.backend_url}/api/v1/auth/me")

            assert resp.status_code == 200, f"Get me failed: {resp.text}"
            data = resp.json()
            assert data.get("success"), f"Get me not successful: {data}"
            assert data.get("data", {}).get("email") == ctx.test_email

    async def _test_verify_role(self, ctx: TestContext):
        """驗證用戶角色正確"""
        async with httpx.AsyncClient(cookies=ctx.cookies, **self.client_kwargs) as client:
            resp = await client.get(f"{self.backend_url}/api/v1/auth/me")

            assert resp.status_code == 200, f"Get me failed: {resp.text}"
            data = resp.json()
            user_role = data.get("data", {}).get("role")
            assert user_role == ctx.test_role, f"Expected role '{ctx.test_role}', got '{user_role}'"

    async def _test_get_sessions(self, ctx: TestContext):
        """測試取得用戶 Sessions"""
        async with httpx.AsyncClient(cookies=ctx.cookies, **self.client_kwargs) as client:
            resp = await client.get(f"{self.backend_url}/api/v1/auth/sessions")

            assert resp.status_code == 200, f"Get sessions failed: {resp.text}"
            data = resp.json()
            assert data.get("total", 0) >= 1 or len(data.get("sessions", [])) >= 1, "Should have at least 1 session"

    async def _test_refresh_token(self, ctx: TestContext):
        """測試刷新 Token"""
        async with httpx.AsyncClient(cookies=ctx.cookies, **self.client_kwargs) as client:
            resp = await client.post(f"{self.backend_url}/api/v1/auth/refresh")

            assert resp.status_code == 200, f"Refresh failed: {resp.text}"
            data = resp.json()
            assert data.get("success"), f"Refresh not successful: {data}"

            ctx.cookies.update(dict(resp.cookies))

    async def _test_logout(self, ctx: TestContext):
        """測試登出"""
        async with httpx.AsyncClient(cookies=ctx.cookies, **self.client_kwargs) as client:
            resp = await client.post(
                f"{self.backend_url}/api/v1/auth/logout",
                json={"logout_all_devices": False}
            )

            assert resp.status_code == 200, f"Logout failed: {resp.text}"
            data = resp.json()
            assert data.get("success"), f"Logout not successful: {data}"

    async def _test_access_after_logout(self, ctx: TestContext):
        """測試登出後存取（應該失敗）"""
        async with httpx.AsyncClient(**self.client_kwargs) as client:
            resp = await client.get(f"{self.backend_url}/api/v1/auth/me")
            assert resp.status_code == 401, f"Expected 401 after logout, got {resp.status_code}"

    # ========== 清理功能 ==========

    async def cleanup_test_data(self):
        """清理所有測試資料"""
        print(f"\n{'='*60}")
        print("🧹 Cleaning up test data...")
        print(f"{'='*60}\n")

        # 1. 刪除此次測試建立的用戶
        for user_id in self.created_user_ids:
            await self._delete_user_by_id(user_id)

        # 2. 查找並刪除所有測試用戶
        await self._cleanup_all_test_users()

        print("\n✅ Cleanup completed\n")

    async def _delete_user_by_id(self, user_id: str):
        """透過 ID 刪除用戶（包含關聯表）"""
        print(f"  Deleting user by ID: {user_id[:8]}...")

        async with httpx.AsyncClient(**self.client_kwargs) as client:
            # 先查詢 user_profiles 取得關聯的 entity ID
            entity_ids = {"student_id": None, "teacher_id": None, "employee_id": None}
            profile_resp = await client.get(
                f"{self.supabase_url}/rest/v1/user_profiles?id=eq.{user_id}&select=*",
                headers={
                    "Authorization": f"Bearer {self.service_role_key}",
                    "apikey": self.service_role_key
                }
            )

            if profile_resp.status_code == 200:
                profiles = profile_resp.json()
                if profiles:
                    profile = profiles[0]
                    entity_ids["student_id"] = profile.get("student_id")
                    entity_ids["teacher_id"] = profile.get("teacher_id")
                    entity_ids["employee_id"] = profile.get("employee_id")

            # 刪除順序很重要：先刪除有外鍵引用的表，再刪除被引用的表
            # 1. 刪除 line_user_bindings (使用 user_id)
            await self._delete_from_table_by_column(client, "line_user_bindings", "user_id", user_id)

            # 2. 刪除 user_profiles (使用 id) - 這會移除對 students/teachers/employees 的 FK 引用
            await self._delete_from_table_by_column(client, "user_profiles", "id", user_id)

            # 3. 刪除關聯的實體記錄
            if entity_ids["student_id"]:
                await self._delete_entity(client, "students", entity_ids["student_id"])
            if entity_ids["teacher_id"]:
                await self._delete_entity(client, "teachers", entity_ids["teacher_id"])
            if entity_ids["employee_id"]:
                await self._delete_entity(client, "employees", entity_ids["employee_id"])

            # 4. 最後刪除 auth.users
            resp = await client.delete(
                f"{self.supabase_url}/auth/v1/admin/users/{user_id}",
                headers={
                    "Authorization": f"Bearer {self.service_role_key}",
                    "apikey": self.service_role_key
                }
            )

            if resp.status_code in (200, 204):
                print(f"    ✅ User {user_id[:8]}... deleted")
            elif resp.status_code == 404:
                print(f"    ⚠️  User {user_id[:8]}... not found")
            else:
                print(f"    ❌ Failed to delete user: {resp.status_code} - {resp.text}")

    async def _delete_entity(self, client: httpx.AsyncClient, table: str, entity_id: str):
        """刪除實體記錄（students/teachers/employees）"""
        resp = await client.delete(
            f"{self.supabase_url}/rest/v1/{table}?id=eq.{entity_id}",
            headers={
                "Authorization": f"Bearer {self.service_role_key}",
                "apikey": self.service_role_key,
                "Prefer": "return=minimal"
            }
        )

        if resp.status_code not in (200, 204, 404):
            print(f"    ⚠️  Failed to delete from {table}: {resp.status_code}")

    async def _delete_from_table_by_column(self, client: httpx.AsyncClient, table: str, column: str, value: str):
        """從指定表按指定欄位刪除資料"""
        resp = await client.delete(
            f"{self.supabase_url}/rest/v1/{table}?{column}=eq.{value}",
            headers={
                "Authorization": f"Bearer {self.service_role_key}",
                "apikey": self.service_role_key,
                "Prefer": "return=minimal"
            }
        )

        if resp.status_code not in (200, 204, 404):
            # 只在真正錯誤時顯示
            if resp.status_code not in (406,):  # 406 可能是沒有匹配的記錄
                print(f"    ⚠️  Failed to delete from {table}: {resp.status_code}")

    async def _cleanup_all_test_users(self):
        """清理所有測試用戶"""
        print(f"  Searching for test users with prefix: {TEST_EMAIL_PREFIX}...")

        async with httpx.AsyncClient(**self.client_kwargs) as client:
            resp = await client.get(
                f"{self.supabase_url}/auth/v1/admin/users",
                headers={
                    "Authorization": f"Bearer {self.service_role_key}",
                    "apikey": self.service_role_key
                },
                params={"per_page": 1000}
            )

            if resp.status_code != 200:
                print(f"    ❌ Failed to list users: {resp.status_code}")
                return

            data = resp.json()
            users = data.get("users", [])

            test_users = [
                u for u in users
                if u.get("email", "").startswith(TEST_EMAIL_PREFIX)
            ]

            if not test_users:
                print("    No test users found")
                return

            print(f"    Found {len(test_users)} test user(s)")

            for user in test_users:
                await self._delete_user_by_id(user["id"])


async def main():
    parser = argparse.ArgumentParser(description="Live Authentication Test Script (Multi-Role)")
    parser.add_argument(
        "--roles",
        nargs="+",
        default=SUPPORTED_ROLES,
        choices=SUPPORTED_ROLES,
        help=f"Roles to test (default: {' '.join(SUPPORTED_ROLES)})"
    )
    parser.add_argument(
        "--cleanup-only",
        action="store_true",
        help="Only cleanup test data without running tests"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Run tests without cleanup"
    )
    parser.add_argument(
        "--backend-url",
        default=BACKEND_URL,
        help=f"Backend URL (default: {BACKEND_URL})"
    )

    args = parser.parse_args()

    tester = LiveAuthTester(
        backend_url=args.backend_url,
        supabase_url=SUPABASE_URL,
        service_role_key=SERVICE_ROLE_KEY,
        roles=args.roles
    )

    if args.cleanup_only:
        await tester.cleanup_test_data()
        return

    success = await tester.run_all_tests()

    if not args.no_cleanup:
        await tester.cleanup_test_data()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
