#!/usr/bin/env python3
"""
Line Messaging API 測試腳本

測試 Line 訊息發送功能，包含：
1. 直接透過 Line API 發送訊息
2. 透過後端 API 發送測試通知

使用前請確保：
1. 在 .env 設定 LINE_*_MESSAGING_TOKEN
2. 有已綁定 Line 的用戶（用於後端 API 測試）

使用方式:
    # 測試直接發送（需要提供 Line User ID）
    python tests/live_line_test.py --direct --line-user-id U1234567890 --channel student

    # 測試後端 API（需要先登入）
    python tests/live_line_test.py --api --email test@example.com --password testpass

    # 檢查設定狀態
    python tests/live_line_test.py --check-config
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

# Line Messaging API
LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"

# 從環境變數取得 Token（或從 .env）
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

# Line Tokens
LINE_TOKENS = {
    "student": os.getenv("LINE_STUDENT_MESSAGING_TOKEN", ""),
    "teacher": os.getenv("LINE_TEACHER_MESSAGING_TOKEN", ""),
    "employee": os.getenv("LINE_EMPLOYEE_MESSAGING_TOKEN", ""),
}


@dataclass
class TestResult:
    name: str
    passed: bool
    message: str = ""
    duration_ms: float = 0


class LineMessageTester:
    def __init__(self, backend_url: str):
        self.backend_url = backend_url.rstrip("/")
        self.results: list[TestResult] = []
        self.cookies: dict = {}

    def check_config(self):
        """檢查 Line 設定狀態"""
        print("\n" + "=" * 60)
        print("🔍 Line Messaging 設定檢查")
        print("=" * 60 + "\n")

        channels = ["student", "teacher", "employee"]
        all_configured = False

        for channel in channels:
            token = LINE_TOKENS.get(channel, "")
            if token:
                # 只顯示前 10 個字元
                masked = token[:10] + "..." if len(token) > 10 else token
                print(f"  ✅ {channel.upper()}: 已設定 ({masked})")
                all_configured = True
            else:
                print(f"  ❌ {channel.upper()}: 未設定")

        print()

        if not all_configured:
            print("⚠️  沒有任何頻道設定 Messaging Token")
            print("\n請在 .env 檔案中設定以下變數：")
            print("  LINE_STUDENT_MESSAGING_TOKEN=your-token")
            print("  LINE_TEACHER_MESSAGING_TOKEN=your-token")
            print("  LINE_EMPLOYEE_MESSAGING_TOKEN=your-token")
            print("\nToken 可從 Line Developers Console 取得：")
            print("  https://developers.line.biz/")
            return False

        return True

    async def test_direct_send(self, line_user_id: str, channel: str, message: str = None):
        """直接透過 Line API 發送訊息"""
        print("\n" + "=" * 60)
        print(f"📤 直接發送測試訊息 (頻道: {channel})")
        print("=" * 60 + "\n")

        token = LINE_TOKENS.get(channel, "")
        if not token:
            print(f"❌ {channel} 頻道的 Messaging Token 未設定")
            return False

        if not message:
            message = f"🧪 測試訊息\n\n發送時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n頻道: {channel}\n\n這是來自系統的測試通知。"

        print(f"  Line User ID: {line_user_id}")
        print(f"  頻道: {channel}")
        print(f"  訊息長度: {len(message)} 字元")
        print()

        async with httpx.AsyncClient(timeout=30.0) as client:
            start = datetime.now()

            response = await client.post(
                LINE_PUSH_URL,
                json={
                    "to": line_user_id,
                    "messages": [{"type": "text", "text": message}],
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                }
            )

            duration = (datetime.now() - start).total_seconds() * 1000

            if response.status_code == 200:
                request_id = response.headers.get("x-line-request-id", "N/A")
                print(f"  ✅ 發送成功！ ({duration:.0f}ms)")
                print(f"  Request ID: {request_id}")
                return True
            else:
                print(f"  ❌ 發送失敗 ({response.status_code})")
                print(f"  回應: {response.text}")
                return False

    async def test_api_send(self, email: str, password: str, channel: str = None, message: str = None):
        """透過後端 API 發送測試訊息"""
        print("\n" + "=" * 60)
        print("📤 透過後端 API 發送測試訊息")
        print("=" * 60 + "\n")

        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. 登入
            print("  ▶ 登入中...")
            resp = await client.post(
                f"{self.backend_url}/api/v1/auth/login",
                json={"email": email, "password": password}
            )

            if resp.status_code != 200:
                print(f"  ❌ 登入失敗: {resp.text}")
                return False

            self.cookies = dict(resp.cookies)
            data = resp.json()
            user_role = data.get("user", {}).get("role", "student")
            print(f"  ✅ 登入成功 (角色: {user_role})")

            # 2. 檢查 Line 綁定狀態
            print("  ▶ 檢查 Line 綁定狀態...")
            target_channel = channel or self._get_channel_from_role(user_role)

            resp = await client.get(
                f"{self.backend_url}/api/v1/auth/line/status",
                params={"channel": target_channel},
                cookies=self.cookies
            )

            if resp.status_code != 200:
                print(f"  ❌ 無法取得綁定狀態: {resp.text}")
                return False

            status_data = resp.json()
            binding = status_data.get("data", {})

            if not binding.get("is_bound"):
                print(f"  ⚠️  尚未綁定 Line {target_channel} 頻道")
                print(f"\n  請先完成 Line 綁定：")
                print(f"  POST {self.backend_url}/api/v1/auth/line/bind?channel={target_channel}")
                return False

            print(f"  ✅ 已綁定 Line: {binding.get('line_display_name', 'N/A')}")

            # 3. 發送測試通知
            print("  ▶ 發送測試通知...")
            test_message = message or f"🧪 測試訊息\n\n發送時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n這是來自系統的測試通知。"

            resp = await client.post(
                f"{self.backend_url}/api/v1/notifications/line/test",
                json={
                    "message": test_message,
                    "channel": target_channel
                },
                cookies=self.cookies
            )

            if resp.status_code != 200:
                print(f"  ❌ 發送失敗: {resp.text}")
                return False

            result = resp.json()
            if result.get("success"):
                print(f"  ✅ 測試通知已發送！")
                print(f"  頻道: {result.get('channel_type', target_channel)}")
                return True
            else:
                print(f"  ❌ 發送失敗: {result.get('message', 'Unknown error')}")
                return False

    async def test_multicast(self, line_user_ids: list[str], channel: str, message: str = None):
        """測試群發訊息"""
        print("\n" + "=" * 60)
        print(f"📤 群發測試訊息 ({len(line_user_ids)} 位用戶)")
        print("=" * 60 + "\n")

        token = LINE_TOKENS.get(channel, "")
        if not token:
            print(f"❌ {channel} 頻道的 Messaging Token 未設定")
            return False

        if not message:
            message = f"🧪 群發測試訊息\n\n發送時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.line.me/v2/bot/message/multicast",
                json={
                    "to": line_user_ids,
                    "messages": [{"type": "text", "text": message}],
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                }
            )

            if response.status_code == 200:
                print(f"  ✅ 群發成功！")
                return True
            else:
                print(f"  ❌ 群發失敗 ({response.status_code}): {response.text}")
                return False

    async def test_rich_message(self, line_user_id: str, channel: str):
        """測試 Flex Message"""
        print("\n" + "=" * 60)
        print("📤 發送 Flex Message 測試")
        print("=" * 60 + "\n")

        token = LINE_TOKENS.get(channel, "")
        if not token:
            print(f"❌ {channel} 頻道的 Messaging Token 未設定")
            return False

        # 建立一個簡單的 Flex Message
        flex_message = {
            "type": "flex",
            "altText": "課程提醒",
            "contents": {
                "type": "bubble",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "📚 課程提醒",
                            "weight": "bold",
                            "size": "lg"
                        }
                    ]
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "您有一堂課程即將開始",
                            "wrap": True
                        },
                        {
                            "type": "separator",
                            "margin": "md"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "margin": "md",
                            "contents": [
                                {"type": "text", "text": "課程", "color": "#888888", "flex": 1},
                                {"type": "text", "text": "英文會話", "flex": 2}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "margin": "sm",
                            "contents": [
                                {"type": "text", "text": "老師", "color": "#888888", "flex": 1},
                                {"type": "text", "text": "王老師", "flex": 2}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "margin": "sm",
                            "contents": [
                                {"type": "text", "text": "時間", "color": "#888888", "flex": 1},
                                {"type": "text", "text": "14:00 - 15:00", "flex": 2}
                            ]
                        }
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "uri",
                                "label": "查看詳情",
                                "uri": "https://example.com"
                            },
                            "style": "primary"
                        }
                    ]
                }
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                LINE_PUSH_URL,
                json={
                    "to": line_user_id,
                    "messages": [flex_message],
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                }
            )

            if response.status_code == 200:
                print(f"  ✅ Flex Message 發送成功！")
                return True
            else:
                print(f"  ❌ 發送失敗 ({response.status_code}): {response.text}")
                return False

    def _get_channel_from_role(self, role: str) -> str:
        """根據角色取得頻道類型"""
        role_to_channel = {
            "student": "student",
            "teacher": "teacher",
            "employee": "employee",
            "admin": "employee",
        }
        return role_to_channel.get(role, "student")


async def main():
    parser = argparse.ArgumentParser(
        description="Line Messaging API 測試腳本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 檢查設定
  python tests/live_line_test.py --check-config

  # 直接發送訊息
  python tests/live_line_test.py --direct --line-user-id U1234567890 --channel student

  # 透過後端 API 發送
  python tests/live_line_test.py --api --email test@example.com --password testpass

  # 發送 Flex Message
  python tests/live_line_test.py --flex --line-user-id U1234567890 --channel student
        """
    )

    parser.add_argument("--check-config", action="store_true", help="檢查 Line 設定狀態")
    parser.add_argument("--direct", action="store_true", help="直接透過 Line API 發送")
    parser.add_argument("--api", action="store_true", help="透過後端 API 發送")
    parser.add_argument("--flex", action="store_true", help="發送 Flex Message 測試")

    parser.add_argument("--line-user-id", help="Line User ID (用於直接發送)")
    parser.add_argument("--channel", choices=["student", "teacher", "employee"], default="student", help="頻道類型")
    parser.add_argument("--message", help="自訂訊息內容")

    parser.add_argument("--email", help="登入 Email (用於後端 API)")
    parser.add_argument("--password", help="登入密碼 (用於後端 API)")

    parser.add_argument("--backend-url", default=BACKEND_URL, help=f"後端 URL (預設: {BACKEND_URL})")

    args = parser.parse_args()

    tester = LineMessageTester(args.backend_url)

    # 預設為 --check-config
    if not any([args.check_config, args.direct, args.api, args.flex]):
        args.check_config = True

    if args.check_config:
        tester.check_config()

    if args.direct:
        if not args.line_user_id:
            print("❌ 請提供 --line-user-id 參數")
            sys.exit(1)
        success = await tester.test_direct_send(args.line_user_id, args.channel, args.message)
        sys.exit(0 if success else 1)

    if args.api:
        if not args.email or not args.password:
            print("❌ 請提供 --email 和 --password 參數")
            sys.exit(1)
        success = await tester.test_api_send(args.email, args.password, args.channel, args.message)
        sys.exit(0 if success else 1)

    if args.flex:
        if not args.line_user_id:
            print("❌ 請提供 --line-user-id 參數")
            sys.exit(1)
        success = await tester.test_rich_message(args.line_user_id, args.channel)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
