#!/usr/bin/env python3
"""
Courses CRUD API 測試腳本

測試課程管理功能，包含：
1. 列出課程 (List)
2. 建立課程 (Create) - 需要 employee/admin 權限
3. 取得單一課程 (Read)
4. 更新課程 (Update) - 需要 employee/admin 權限
5. 刪除課程 (Delete) - 需要 employee/admin 權限

使用方式:
    # 執行完整 CRUD 測試（需要 employee/admin 帳號）
    python tests/live_courses_test.py --email employee@example.com --password testpass

    # 只測試列表和讀取（任何登入用戶）
    python tests/live_courses_test.py --email student@example.com --password testpass --read-only

    # 保留測試建立的課程（不刪除）
    python tests/live_courses_test.py --email employee@example.com --password testpass --no-cleanup

    # 自訂後端 URL
    python tests/live_courses_test.py --email admin@example.com --password testpass --backend-url http://localhost:8001
"""

import httpx
import asyncio
import argparse
import sys
import os
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

# 設定
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8001")


def load_env():
    """載入 .env 檔案"""
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())


load_env()


@dataclass
class TestResult:
    name: str
    passed: bool
    message: str = ""
    duration_ms: float = 0


@dataclass
class CreatedCourse:
    id: str
    course_code: str
    course_name: str


class CoursesCRUDTester:
    def __init__(self, backend_url: str, no_cleanup: bool = False):
        self.backend_url = backend_url.rstrip("/")
        self.results: list[TestResult] = []
        self.cookies: dict = {}
        self.no_cleanup = no_cleanup
        self.created_courses: list[CreatedCourse] = []
        self.user_role: str = ""

    def _record_result(self, name: str, passed: bool, message: str = "", duration_ms: float = 0):
        """記錄測試結果"""
        self.results.append(TestResult(name, passed, message, duration_ms))
        status = "✅" if passed else "❌"
        duration_str = f" ({duration_ms:.0f}ms)" if duration_ms else ""
        print(f"  {status} {name}{duration_str}")
        if message and not passed:
            print(f"     └─ {message}")

    async def login(self, email: str, password: str) -> bool:
        """登入並取得 session"""
        print("\n" + "=" * 60)
        print("🔐 登入")
        print("=" * 60 + "\n")

        async with httpx.AsyncClient(timeout=30.0) as client:
            start = datetime.now()
            resp = await client.post(
                f"{self.backend_url}/api/v1/auth/login",
                json={"email": email, "password": password}
            )
            duration = (datetime.now() - start).total_seconds() * 1000

            if resp.status_code == 200:
                self.cookies = dict(resp.cookies)
                data = resp.json()
                self.user_role = data.get("user", {}).get("role", "student")
                self._record_result(
                    f"登入成功 (角色: {self.user_role})",
                    True,
                    duration_ms=duration
                )
                return True
            else:
                self._record_result(
                    "登入",
                    False,
                    f"狀態碼: {resp.status_code}, 回應: {resp.text}",
                    duration_ms=duration
                )
                return False

    async def test_list_courses(self) -> bool:
        """測試列出課程"""
        print("\n" + "=" * 60)
        print("📋 測試列出課程 (List)")
        print("=" * 60 + "\n")

        async with httpx.AsyncClient(timeout=30.0) as client:
            # 測試基本列表
            start = datetime.now()
            resp = await client.get(
                f"{self.backend_url}/api/v1/courses",
                cookies=self.cookies
            )
            duration = (datetime.now() - start).total_seconds() * 1000

            if resp.status_code == 200:
                data = resp.json()
                total = data.get("total", 0)
                courses = data.get("data", [])
                self._record_result(
                    f"列出課程 (共 {total} 筆)",
                    True,
                    duration_ms=duration
                )
            else:
                self._record_result(
                    "列出課程",
                    False,
                    f"狀態碼: {resp.status_code}",
                    duration_ms=duration
                )
                return False

            # 測試分頁
            start = datetime.now()
            resp = await client.get(
                f"{self.backend_url}/api/v1/courses",
                params={"page": 1, "per_page": 5},
                cookies=self.cookies
            )
            duration = (datetime.now() - start).total_seconds() * 1000

            if resp.status_code == 200:
                data = resp.json()
                self._record_result(
                    f"分頁查詢 (page=1, per_page=5)",
                    True,
                    duration_ms=duration
                )
            else:
                self._record_result(
                    "分頁查詢",
                    False,
                    f"狀態碼: {resp.status_code}",
                    duration_ms=duration
                )

            # 測試篩選 is_active
            start = datetime.now()
            resp = await client.get(
                f"{self.backend_url}/api/v1/courses",
                params={"is_active": True},
                cookies=self.cookies
            )
            duration = (datetime.now() - start).total_seconds() * 1000

            if resp.status_code == 200:
                self._record_result(
                    "篩選啟用課程 (is_active=true)",
                    True,
                    duration_ms=duration
                )
            else:
                self._record_result(
                    "篩選啟用課程",
                    False,
                    f"狀態碼: {resp.status_code}",
                    duration_ms=duration
                )

            # 測試搜尋
            start = datetime.now()
            resp = await client.get(
                f"{self.backend_url}/api/v1/courses",
                params={"search": "test"},
                cookies=self.cookies
            )
            duration = (datetime.now() - start).total_seconds() * 1000

            if resp.status_code == 200:
                self._record_result(
                    "搜尋課程 (search='test')",
                    True,
                    duration_ms=duration
                )
            else:
                self._record_result(
                    "搜尋課程",
                    False,
                    f"狀態碼: {resp.status_code}",
                    duration_ms=duration
                )

        return True

    async def test_create_course(self) -> Optional[str]:
        """測試建立課程"""
        print("\n" + "=" * 60)
        print("➕ 測試建立課程 (Create)")
        print("=" * 60 + "\n")

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        course_data = {
            "course_code": f"TEST{timestamp}",
            "course_name": f"測試課程 {timestamp}",
            "description": "這是自動化測試建立的課程",
            "duration_minutes": 90,
            "is_active": True
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            start = datetime.now()
            resp = await client.post(
                f"{self.backend_url}/api/v1/courses",
                json=course_data,
                cookies=self.cookies
            )
            duration = (datetime.now() - start).total_seconds() * 1000

            if resp.status_code == 200:
                data = resp.json()
                course = data.get("data", {})
                course_id = course.get("id")

                self.created_courses.append(CreatedCourse(
                    id=course_id,
                    course_code=course_data["course_code"],
                    course_name=course_data["course_name"]
                ))

                self._record_result(
                    f"建立課程成功 (ID: {course_id[:8]}...)",
                    True,
                    duration_ms=duration
                )
                print(f"     └─ 課程代碼: {course.get('course_code')}")
                print(f"     └─ 課程名稱: {course.get('course_name')}")
                return course_id
            elif resp.status_code == 403:
                self._record_result(
                    "建立課程",
                    False,
                    "權限不足 (需要 employee/admin 角色)",
                    duration_ms=duration
                )
                return None
            else:
                self._record_result(
                    "建立課程",
                    False,
                    f"狀態碼: {resp.status_code}, 回應: {resp.text}",
                    duration_ms=duration
                )
                return None

    async def test_create_duplicate_course(self, course_code: str) -> bool:
        """測試建立重複課程代碼（應該失敗）"""
        print("\n" + "=" * 60)
        print("🔄 測試建立重複課程代碼")
        print("=" * 60 + "\n")

        course_data = {
            "course_code": course_code,
            "course_name": "重複測試課程",
            "description": "這應該要失敗",
            "duration_minutes": 60,
            "is_active": True
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            start = datetime.now()
            resp = await client.post(
                f"{self.backend_url}/api/v1/courses",
                json=course_data,
                cookies=self.cookies
            )
            duration = (datetime.now() - start).total_seconds() * 1000

            if resp.status_code == 400:
                self._record_result(
                    "重複課程代碼被正確拒絕",
                    True,
                    duration_ms=duration
                )
                return True
            else:
                self._record_result(
                    "重複課程代碼驗證",
                    False,
                    f"預期 400，實際 {resp.status_code}",
                    duration_ms=duration
                )
                return False

    async def test_get_course(self, course_id: str) -> bool:
        """測試取得單一課程"""
        print("\n" + "=" * 60)
        print("🔍 測試取得單一課程 (Read)")
        print("=" * 60 + "\n")

        async with httpx.AsyncClient(timeout=30.0) as client:
            # 測試取得存在的課程
            start = datetime.now()
            resp = await client.get(
                f"{self.backend_url}/api/v1/courses/{course_id}",
                cookies=self.cookies
            )
            duration = (datetime.now() - start).total_seconds() * 1000

            if resp.status_code == 200:
                data = resp.json()
                course = data.get("data", {})
                self._record_result(
                    f"取得課程 ({course.get('course_name', 'N/A')})",
                    True,
                    duration_ms=duration
                )
            else:
                self._record_result(
                    "取得課程",
                    False,
                    f"狀態碼: {resp.status_code}",
                    duration_ms=duration
                )
                return False

            # 測試取得不存在的課程
            fake_id = "00000000-0000-0000-0000-000000000000"
            start = datetime.now()
            resp = await client.get(
                f"{self.backend_url}/api/v1/courses/{fake_id}",
                cookies=self.cookies
            )
            duration = (datetime.now() - start).total_seconds() * 1000

            if resp.status_code == 404:
                self._record_result(
                    "不存在的課程返回 404",
                    True,
                    duration_ms=duration
                )
            else:
                self._record_result(
                    "不存在的課程檢查",
                    False,
                    f"預期 404，實際 {resp.status_code}",
                    duration_ms=duration
                )

        return True

    async def test_update_course(self, course_id: str) -> bool:
        """測試更新課程"""
        print("\n" + "=" * 60)
        print("✏️  測試更新課程 (Update)")
        print("=" * 60 + "\n")

        update_data = {
            "course_name": f"已更新的課程 {datetime.now().strftime('%H:%M:%S')}",
            "description": "這個描述已經被更新",
            "duration_minutes": 120,
            "is_active": False
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            start = datetime.now()
            resp = await client.put(
                f"{self.backend_url}/api/v1/courses/{course_id}",
                json=update_data,
                cookies=self.cookies
            )
            duration = (datetime.now() - start).total_seconds() * 1000

            if resp.status_code == 200:
                data = resp.json()
                course = data.get("data", {})
                self._record_result(
                    f"更新課程成功",
                    True,
                    duration_ms=duration
                )
                print(f"     └─ 新名稱: {course.get('course_name')}")
                print(f"     └─ 新時長: {course.get('duration_minutes')} 分鐘")
                print(f"     └─ 狀態: {'啟用' if course.get('is_active') else '停用'}")

                # 驗證更新結果
                if course.get("duration_minutes") == 120 and not course.get("is_active"):
                    self._record_result("更新資料驗證", True)
                else:
                    self._record_result("更新資料驗證", False, "更新後的資料與預期不符")

                return True
            elif resp.status_code == 403:
                self._record_result(
                    "更新課程",
                    False,
                    "權限不足 (需要 employee/admin 角色)",
                    duration_ms=duration
                )
                return False
            else:
                self._record_result(
                    "更新課程",
                    False,
                    f"狀態碼: {resp.status_code}, 回應: {resp.text}",
                    duration_ms=duration
                )
                return False

    async def test_update_nonexistent_course(self) -> bool:
        """測試更新不存在的課程"""
        print("\n" + "=" * 60)
        print("🔄 測試更新不存在的課程")
        print("=" * 60 + "\n")

        fake_id = "00000000-0000-0000-0000-000000000000"
        update_data = {"course_name": "Should Fail"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            start = datetime.now()
            resp = await client.put(
                f"{self.backend_url}/api/v1/courses/{fake_id}",
                json=update_data,
                cookies=self.cookies
            )
            duration = (datetime.now() - start).total_seconds() * 1000

            if resp.status_code == 404:
                self._record_result(
                    "不存在的課程返回 404",
                    True,
                    duration_ms=duration
                )
                return True
            else:
                self._record_result(
                    "不存在的課程檢查",
                    False,
                    f"預期 404，實際 {resp.status_code}",
                    duration_ms=duration
                )
                return False

    async def test_delete_course(self, course_id: str) -> bool:
        """測試刪除課程"""
        print("\n" + "=" * 60)
        print("🗑️  測試刪除課程 (Delete)")
        print("=" * 60 + "\n")

        async with httpx.AsyncClient(timeout=30.0) as client:
            start = datetime.now()
            resp = await client.delete(
                f"{self.backend_url}/api/v1/courses/{course_id}",
                cookies=self.cookies
            )
            duration = (datetime.now() - start).total_seconds() * 1000

            if resp.status_code == 200:
                self._record_result(
                    "刪除課程成功",
                    True,
                    duration_ms=duration
                )

                # 驗證課程已被刪除（應該返回 404）
                start = datetime.now()
                resp = await client.get(
                    f"{self.backend_url}/api/v1/courses/{course_id}",
                    cookies=self.cookies
                )
                duration = (datetime.now() - start).total_seconds() * 1000

                if resp.status_code == 404:
                    self._record_result(
                        "刪除後課程不可存取",
                        True,
                        duration_ms=duration
                    )
                else:
                    self._record_result(
                        "刪除後課程檢查",
                        False,
                        f"預期 404，實際 {resp.status_code}",
                        duration_ms=duration
                    )

                return True
            elif resp.status_code == 403:
                self._record_result(
                    "刪除課程",
                    False,
                    "權限不足 (需要 employee/admin 角色)",
                    duration_ms=duration
                )
                return False
            else:
                self._record_result(
                    "刪除課程",
                    False,
                    f"狀態碼: {resp.status_code}, 回應: {resp.text}",
                    duration_ms=duration
                )
                return False

    async def cleanup(self):
        """清理測試建立的課程"""
        if self.no_cleanup:
            print("\n" + "=" * 60)
            print("📝 已建立的課程（保留不刪除）")
            print("=" * 60 + "\n")
            for course in self.created_courses:
                print(f"  ID: {course.id}")
                print(f"  課程代碼: {course.course_code}")
                print(f"  課程名稱: {course.course_name}")
                print()
            return

        if not self.created_courses:
            return

        print("\n" + "=" * 60)
        print("🧹 清理測試資料")
        print("=" * 60 + "\n")

        async with httpx.AsyncClient(timeout=30.0) as client:
            for course in self.created_courses:
                resp = await client.delete(
                    f"{self.backend_url}/api/v1/courses/{course.id}",
                    cookies=self.cookies
                )
                if resp.status_code == 200:
                    print(f"  ✅ 已刪除: {course.course_name}")
                elif resp.status_code == 404:
                    print(f"  ⏭️  已刪除 (測試中刪除): {course.course_name}")
                else:
                    print(f"  ❌ 刪除失敗: {course.course_name}")

    def print_summary(self):
        """列印測試摘要"""
        print("\n" + "=" * 60)
        print("📊 測試摘要")
        print("=" * 60 + "\n")

        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)

        print(f"  總計: {total} 項測試")
        print(f"  通過: {passed} ✅")
        print(f"  失敗: {failed} ❌")
        print(f"  成功率: {passed/total*100:.1f}%" if total > 0 else "  成功率: N/A")
        print()

        if failed > 0:
            print("  失敗的測試:")
            for r in self.results:
                if not r.passed:
                    print(f"    - {r.name}: {r.message}")
            print()

        return failed == 0


async def main():
    parser = argparse.ArgumentParser(
        description="Courses CRUD API 測試腳本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 完整 CRUD 測試（需要 employee/admin 帳號）
  python tests/live_courses_test.py --email employee@example.com --password testpass

  # 只測試列表和讀取
  python tests/live_courses_test.py --email student@example.com --password testpass --read-only

  # 保留測試建立的課程
  python tests/live_courses_test.py --email employee@example.com --password testpass --no-cleanup
        """
    )

    parser.add_argument("--email", required=True, help="登入 Email")
    parser.add_argument("--password", required=True, help="登入密碼")
    parser.add_argument("--backend-url", default=BACKEND_URL, help=f"後端 URL (預設: {BACKEND_URL})")
    parser.add_argument("--read-only", action="store_true", help="只測試讀取功能（不需要 staff 權限）")
    parser.add_argument("--no-cleanup", action="store_true", help="保留測試建立的課程")

    args = parser.parse_args()

    tester = CoursesCRUDTester(args.backend_url, no_cleanup=args.no_cleanup)

    print("\n" + "🚀" * 20)
    print("\n   Courses CRUD API 測試")
    print(f"   後端: {args.backend_url}")
    print(f"   模式: {'唯讀' if args.read_only else '完整 CRUD'}")
    print("\n" + "🚀" * 20)

    try:
        # 1. 登入
        if not await tester.login(args.email, args.password):
            tester.print_summary()
            sys.exit(1)

        # 2. 測試列出課程
        await tester.test_list_courses()

        if args.read_only:
            # 唯讀模式：只測試列表
            tester.print_summary()
            sys.exit(0 if all(r.passed for r in tester.results) else 1)

        # 檢查是否有權限進行 CRUD
        if tester.user_role not in ["admin", "employee"]:
            print("\n⚠️  目前角色為 '{}'，無法執行建立/更新/刪除測試".format(tester.user_role))
            print("   請使用 --read-only 模式或改用 employee/admin 帳號")
            tester.print_summary()
            sys.exit(1)

        # 3. 測試建立課程
        course_id = await tester.test_create_course()

        if course_id:
            # 4. 測試重複課程代碼
            await tester.test_create_duplicate_course(tester.created_courses[0].course_code)

            # 5. 測試取得課程
            await tester.test_get_course(course_id)

            # 6. 測試更新課程
            await tester.test_update_course(course_id)

            # 7. 測試更新不存在的課程
            await tester.test_update_nonexistent_course()

            # 8. 測試刪除課程（如果不是 no_cleanup 模式）
            if not args.no_cleanup:
                await tester.test_delete_course(course_id)
                # 從 created_courses 移除已刪除的課程
                tester.created_courses = [c for c in tester.created_courses if c.id != course_id]

        # 清理
        await tester.cleanup()

        # 列印摘要
        success = tester.print_summary()
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  測試中斷")
        await tester.cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 測試發生錯誤: {e}")
        await tester.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
