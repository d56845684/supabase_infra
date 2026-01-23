#!/usr/bin/env python3
"""
Line 綁定功能測試腳本

測試 Line 綁定相關功能，包含：
1. 檢查 Line OAuth 設定
2. 取得 Line 登入 URL
3. 取得綁定 URL（已登入用戶）
4. 檢查綁定狀態
5. 解除綁定

使用方式:
    # 檢查設定
    python tests/live_line_binding_test.py --check-config

    # 取得 Line 登入 URL
    python tests/live_line_binding_test.py --login-url --channel student

    # 已登入用戶取得綁定 URL
    python tests/live_line_binding_test.py --bind-url --email test@example.com --password testpass

    # 檢查綁定狀態
    python tests/live_line_binding_test.py --status --email test@example.com --password testpass

    # 執行完整測試流程
    python tests/live_line_binding_test.py --full-test --email test@example.com --password testpass
"""

import httpx
import asyncio
import argparse
import sys
import os
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

# 設定
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8001")

# 從環境變數取得設定
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

# Line Login 設定（所有角色共用）
LINE_LOGIN_CONFIG = {
    "channel_id": os.getenv("LINE_LOGIN_CHANNEL_ID", ""),
    "channel_secret": os.getenv("LINE_LOGIN_CHANNEL_SECRET", ""),
    "callback_url": os.getenv("LINE_LOGIN_CALLBACK_URL", "http://localhost:8001/api/v1/auth/line/callback"),
}

# Line Messaging 設定（每個角色使用不同的 Token）
LINE_MESSAGING_TOKENS = {
    "student": os.getenv("LINE_STUDENT_MESSAGING_TOKEN", ""),
    "teacher": os.getenv("LINE_TEACHER_MESSAGING_TOKEN", ""),
    "employee": os.getenv("LINE_EMPLOYEE_MESSAGING_TOKEN", ""),
}


class LineBindingTester:
    def __init__(self, backend_url: str):
        self.backend_url = backend_url.rstrip("/")
        self.cookies: dict = {}
        self.user_info: dict = {}

    def check_config(self):
        """檢查 Line OAuth 設定狀態"""
        print("\n" + "=" * 60)
        print("🔍 Line 設定檢查")
        print("=" * 60 + "\n")

        # 檢查 Line Login（所有角色共用）
        print("📱 Line Login（登入認證 - 所有角色共用）:")
        channel_id = LINE_LOGIN_CONFIG["channel_id"]
        channel_secret = LINE_LOGIN_CONFIG["channel_secret"]
        callback_url = LINE_LOGIN_CONFIG["callback_url"]

        login_configured = bool(channel_id and channel_secret)

        if login_configured:
            print(f"  ✅ 已設定")
            print(f"     Channel ID: {channel_id[:6]}*** ({len(channel_id)} chars)")
            print(f"     Secret: {'*' * 6}*** ({len(channel_secret)} chars)")
            print(f"     Callback: {callback_url}")
        else:
            missing = []
            if not channel_id:
                missing.append("LINE_LOGIN_CHANNEL_ID")
            if not channel_secret:
                missing.append("LINE_LOGIN_CHANNEL_SECRET")
            print(f"  ❌ 未設定 ({', '.join(missing)})")

        print()

        # 檢查 Line Messaging（每個角色不同）
        print("📨 Line Messaging（發送通知 - 每個角色獨立）:")
        any_messaging = False
        for channel, token in LINE_MESSAGING_TOKENS.items():
            if token:
                any_messaging = True
                print(f"  ✅ {channel.upper()}: {token[:20]}*** ({len(token)} chars)")
            else:
                print(f"  ⚪ {channel.upper()}: 未設定（選填）")

        print()

        if not login_configured:
            print("⚠️  Line Login 未設定")
            print("\n請在 .env 檔案中設定以下變數：")
            print("  LINE_LOGIN_CHANNEL_ID=your-channel-id")
            print("  LINE_LOGIN_CHANNEL_SECRET=your-channel-secret")
            print("  LINE_LOGIN_CALLBACK_URL=http://localhost:8001/api/v1/auth/line/callback")
            print("\n從 Line Developers Console 取得：")
            print("  https://developers.line.biz/")
            return False

        return True

    async def login(self, email: str, password: str) -> bool:
        """登入系統"""
        print(f"  ▶ 登入中... ({email})")

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.backend_url}/api/v1/auth/login",
                json={"email": email, "password": password}
            )

            if resp.status_code != 200:
                print(f"  ❌ 登入失敗: {resp.text}")
                return False

            self.cookies = dict(resp.cookies)
            data = resp.json()

            if not data.get("success"):
                print(f"  ❌ 登入失敗: {data.get('message')}")
                return False

            self.user_info = data.get("user", {})
            print(f"  ✅ 登入成功")
            print(f"     用戶 ID: {self.user_info.get('id', 'N/A')[:8]}...")
            print(f"     角色: {self.user_info.get('role', 'N/A')}")
            return True

    async def get_login_url(self, channel: str) -> Optional[str]:
        """取得 Line 登入 URL"""
        print("\n" + "=" * 60)
        print(f"🔗 取得 Line 登入 URL (頻道: {channel})")
        print("=" * 60 + "\n")

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{self.backend_url}/api/v1/auth/line/login",
                params={"channel": channel}
            )

            if resp.status_code == 503:
                print(f"  ❌ Line {channel} 頻道未啟用")
                return None

            if resp.status_code != 200:
                print(f"  ❌ 取得失敗: {resp.text}")
                return None

            data = resp.json()
            url = data.get("url", "")
            state = data.get("state", "")

            print(f"  ✅ 成功取得登入 URL")
            print(f"     State: {state[:16]}...")
            print(f"\n  📱 請在瀏覽器開啟以下 URL 進行 Line 登入：")
            print(f"\n  {url}\n")

            return url

    async def get_bind_url(self, channel: str = None) -> Optional[str]:
        """取得 Line 綁定 URL（需要已登入）"""
        print("\n" + "=" * 60)
        print(f"🔗 取得 Line 綁定 URL")
        print("=" * 60 + "\n")

        if not self.cookies:
            print("  ❌ 尚未登入，請先執行登入")
            return None

        # 如果未指定頻道，根據角色決定
        if not channel:
            role = self.user_info.get("role", "student")
            role_to_channel = {
                "student": "student",
                "teacher": "teacher",
                "employee": "employee",
                "admin": "employee",
            }
            channel = role_to_channel.get(role, "student")

        print(f"  頻道: {channel}")

        async with httpx.AsyncClient(timeout=30.0, cookies=self.cookies) as client:
            resp = await client.post(
                f"{self.backend_url}/api/v1/auth/line/bind",
                params={"channel": channel}
            )

            if resp.status_code == 503:
                print(f"  ❌ Line {channel} 頻道未啟用")
                return None

            if resp.status_code != 200:
                print(f"  ❌ 取得失敗: {resp.text}")
                return None

            data = resp.json()

            if not data.get("success"):
                # 可能已經綁定
                binding_data = data.get("data", {})
                if binding_data.get("is_bound"):
                    print(f"  ⚠️  已綁定 Line 帳號")
                    print(f"     顯示名稱: {binding_data.get('line_display_name', 'N/A')}")
                    print(f"     綁定時間: {binding_data.get('bound_at', 'N/A')}")
                    return None
                else:
                    print(f"  ❌ {data.get('message')}")
                    return None

            binding_data = data.get("data", {})
            url = binding_data.get("bind_url", "")

            print(f"  ✅ 成功取得綁定 URL")
            print(f"\n  📱 請在瀏覽器開啟以下 URL 進行 Line 綁定：")
            print(f"\n  {url}\n")

            return url

    async def check_status(self, channel: str = None) -> dict:
        """檢查 Line 綁定狀態"""
        print("\n" + "=" * 60)
        print("📋 Line 綁定狀態")
        print("=" * 60 + "\n")

        if not self.cookies:
            print("  ❌ 尚未登入，請先執行登入")
            return {}

        async with httpx.AsyncClient(timeout=30.0, cookies=self.cookies) as client:
            # 檢查所有頻道綁定
            resp = await client.get(
                f"{self.backend_url}/api/v1/auth/line/bindings"
            )

            if resp.status_code != 200:
                print(f"  ❌ 取得失敗: {resp.text}")
                return {}

            data = resp.json()
            bindings = data.get("bindings", [])

            if not bindings:
                print("  📭 尚未綁定任何 Line 頻道")
            else:
                print(f"  已綁定 {len(bindings)} 個頻道：\n")
                for b in bindings:
                    status = "✅" if b.get("is_bound") else "❌"
                    print(f"  {status} {b.get('channel_type', 'N/A').upper()}:")
                    print(f"     顯示名稱: {b.get('line_display_name', 'N/A')}")
                    if b.get("line_picture_url"):
                        print(f"     頭像: {b.get('line_picture_url')[:50]}...")
                    print(f"     綁定時間: {b.get('bound_at', 'N/A')}")
                    print()

            return data

    async def unbind(self, channel: str) -> bool:
        """解除 Line 綁定"""
        print("\n" + "=" * 60)
        print(f"🔓 解除 Line 綁定 (頻道: {channel})")
        print("=" * 60 + "\n")

        if not self.cookies:
            print("  ❌ 尚未登入，請先執行登入")
            return False

        async with httpx.AsyncClient(timeout=30.0, cookies=self.cookies) as client:
            resp = await client.delete(
                f"{self.backend_url}/api/v1/auth/line/unbind",
                params={"channel": channel}
            )

            if resp.status_code != 200:
                print(f"  ❌ 解除失敗: {resp.text}")
                return False

            data = resp.json()

            if data.get("success"):
                print(f"  ✅ 已解除 Line {channel} 頻道綁定")
                return True
            else:
                print(f"  ❌ {data.get('message')}")
                return False

    async def full_test(self, email: str, password: str, channel: str = "student"):
        """執行完整測試流程"""
        print("\n" + "=" * 60)
        print("🧪 Line 綁定完整測試")
        print("=" * 60)

        # 1. 檢查設定
        print("\n📌 Step 1: 檢查設定")
        if not self.check_config():
            return False

        # 2. 登入
        print("\n📌 Step 2: 登入系統")
        if not await self.login(email, password):
            return False

        # 3. 檢查目前綁定狀態
        print("\n📌 Step 3: 檢查目前綁定狀態")
        await self.check_status()

        # 4. 取得綁定 URL
        print("\n📌 Step 4: 取得綁定 URL")
        bind_url = await self.get_bind_url(channel)

        if bind_url:
            print("\n" + "-" * 60)
            print("🎯 下一步：")
            print("-" * 60)
            print(f"\n1. 在瀏覽器開啟上方的 URL")
            print(f"2. 使用 Line 帳號登入並授權")
            print(f"3. 授權後會自動導向回 callback URL")
            print(f"4. 再次執行 --status 檢查綁定結果")
            print()

        return True

    async def test_callback_simulation(self, channel: str = "student"):
        """模擬 callback 流程（用於開發測試）"""
        print("\n" + "=" * 60)
        print("🔬 Line Callback 模擬測試")
        print("=" * 60 + "\n")

        print("  ⚠️  此功能需要手動在 Line Developers Console 設定")
        print("     Callback URL 才能接收真實的 callback")
        print()
        print("  實際流程：")
        print("  1. 用戶點擊 Line 登入 URL")
        print("  2. Line 顯示授權頁面")
        print("  3. 用戶授權後，Line 導向 callback URL")
        print("  4. Callback URL 格式：")
        print(f"     {self.backend_url}/api/v1/auth/line/callback?code=xxx&state=xxx")
        print("     （channel_type 從 state 中取得）")
        print()
        print("  5. 後端處理：")
        print("     - 驗證 state，從中取得 channel_type")
        print("     - 用 code 交換 access_token")
        print("     - 取得用戶 Line profile")
        print("     - 建立或更新綁定")
        print("     - 導向前端成功頁面")


async def main():
    parser = argparse.ArgumentParser(
        description="Line 綁定功能測試腳本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 檢查設定
  python tests/live_line_binding_test.py --check-config

  # 取得 Line 登入 URL（新用戶或未登入）
  python tests/live_line_binding_test.py --login-url --channel student

  # 取得綁定 URL（已登入用戶）
  python tests/live_line_binding_test.py --bind-url --email test@example.com --password testpass

  # 檢查綁定狀態
  python tests/live_line_binding_test.py --status --email test@example.com --password testpass

  # 解除綁定
  python tests/live_line_binding_test.py --unbind --channel student --email test@example.com --password testpass

  # 完整測試流程
  python tests/live_line_binding_test.py --full-test --email test@example.com --password testpass
        """
    )

    parser.add_argument("--check-config", action="store_true", help="檢查 Line OAuth 設定")
    parser.add_argument("--login-url", action="store_true", help="取得 Line 登入 URL")
    parser.add_argument("--bind-url", action="store_true", help="取得 Line 綁定 URL（需登入）")
    parser.add_argument("--status", action="store_true", help="檢查綁定狀態（需登入）")
    parser.add_argument("--unbind", action="store_true", help="解除綁定（需登入）")
    parser.add_argument("--full-test", action="store_true", help="執行完整測試流程")

    parser.add_argument("--channel", choices=["student", "teacher", "employee"], default="student", help="頻道類型")
    parser.add_argument("--email", help="登入 Email")
    parser.add_argument("--password", help="登入密碼")

    parser.add_argument("--backend-url", default=BACKEND_URL, help=f"後端 URL (預設: {BACKEND_URL})")

    args = parser.parse_args()

    tester = LineBindingTester(args.backend_url)

    # 預設為 --check-config
    if not any([args.check_config, args.login_url, args.bind_url, args.status, args.unbind, args.full_test]):
        args.check_config = True

    if args.check_config:
        tester.check_config()

    if args.login_url:
        await tester.get_login_url(args.channel)

    if args.bind_url:
        if not args.email or not args.password:
            print("❌ 請提供 --email 和 --password 參數")
            sys.exit(1)
        if await tester.login(args.email, args.password):
            await tester.get_bind_url(args.channel)

    if args.status:
        if not args.email or not args.password:
            print("❌ 請提供 --email 和 --password 參數")
            sys.exit(1)
        if await tester.login(args.email, args.password):
            await tester.check_status()

    if args.unbind:
        if not args.email or not args.password:
            print("❌ 請提供 --email 和 --password 參數")
            sys.exit(1)
        if await tester.login(args.email, args.password):
            await tester.unbind(args.channel)

    if args.full_test:
        if not args.email or not args.password:
            print("❌ 請提供 --email 和 --password 參數")
            sys.exit(1)
        await tester.full_test(args.email, args.password, args.channel)


if __name__ == "__main__":
    asyncio.run(main())
