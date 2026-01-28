# Backend Tests

## 目錄結構

```
tests/
├── conftest.py                 # 共用 fixtures
├── live_auth_test.py           # Live 認證測試腳本（真實環境，支援多角色）
├── unit/
│   ├── test_security.py        # 安全模組單元測試
│   └── test_session_service.py # Session 服務單元測試
├── integration/
│   ├── test_auth_api.py        # 認證 API 整合測試
│   ├── test_user_api.py        # 用戶 API 整合測試
│   ├── test_health_api.py      # 健康檢查 API 測試
│   └── test_middleware.py      # 中間件測試
└── e2e/
    ├── test_auth_flow.py       # 認證流程端對端測試
    └── test_permission_flow.py # 權限流程端對端測試
```

## 執行測試

### 單元測試 / 整合測試 (使用 pytest + mock)

```bash
# 執行所有測試
pytest

# 執行特定類型測試
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# 顯示詳細輸出
pytest -v

# 執行特定測試檔案
pytest tests/integration/test_auth_api.py
```

### Live 認證測試 (真實環境，支援多角色)

`live_auth_test.py` 針對實際運行中的服務進行測試，支援多角色測試及自動清理測試資料。

#### 前置條件

確保服務已啟動：
```bash
docker compose up -d
```

#### 使用方式

```bash
# 執行所有角色測試 (student, teacher, admin)
python3 tests/live_auth_test.py

# 測試特定角色
python3 tests/live_auth_test.py --roles student
python3 tests/live_auth_test.py --roles student teacher
python3 tests/live_auth_test.py --roles teacher admin

# 執行測試但不清理測試資料
python3 tests/live_auth_test.py --no-cleanup

# 只清理測試資料（不執行測試）
python3 tests/live_auth_test.py --cleanup-only

# 指定 backend URL
python3 tests/live_auth_test.py --backend-url http://127.0.0.1:8001
```

#### 支援的角色

| 角色 | 說明 |
|------|------|
| `student` | 學生角色 |
| `teacher` | 教師角色 |
| `admin` | 管理員角色 |

#### 測試項目（每個角色）

| 測試項目 | 說明 |
|---------|------|
| Health Check | 健康檢查端點 |
| User Registration | 用戶註冊 |
| User Login | 用戶登入 |
| Get Current User | 取得當前用戶資訊 |
| Verify Role | 驗證用戶角色正確 |
| Get Sessions | 取得用戶 Sessions |
| Token Refresh | 刷新 Token |
| Logout | 用戶登出 |
| Access After Logout | 登出後存取（預期失敗） |

#### 清理機制

測試腳本會：
1. 自動刪除當次測試建立的所有用戶（各角色）
2. 掃描並刪除所有 `test_auth_*@example.com` 格式的測試用戶

#### 環境變數

| 變數 | 預設值 | 說明 |
|-----|-------|------|
| `BACKEND_URL` | `http://127.0.0.1:8001` | Backend API URL |
| `SUPABASE_URL` | `http://127.0.0.1:8000` | Supabase API URL |
| `SERVICE_ROLE_KEY` | (內建) | Supabase Service Role Key |

#### 輸出範例

```
============================================================
🧪 Live Authentication Tests (Multi-Role)
============================================================
Backend URL: http://127.0.0.1:8001
Roles to test: student, teacher, admin
============================================================

────────────────────────────────────────────────────────────
👤 Testing Role: STUDENT
────────────────────────────────────────────────────────────
Test Email: test_auth_student_20260122_151412@example.com

  ▶ Health Check... ✅ (135ms)
  ▶ User Registration... ✅ (261ms)
  ▶ User Login... ✅ (148ms)
  ▶ Get Current User... ✅ (46ms)
  ▶ Verify Role... ✅ (44ms)
  ▶ Get Sessions... ✅ (45ms)
  ▶ Token Refresh... ✅ (49ms)
  ▶ Logout... ✅ (50ms)
  ▶ Access After Logout... ✅ (45ms)

📋 Role 'student': 9 passed, 0 failed

────────────────────────────────────────────────────────────
👤 Testing Role: TEACHER
────────────────────────────────────────────────────────────
Test Email: test_auth_teacher_20260122_151412@example.com

  ▶ Health Check... ✅ (48ms)
  ▶ User Registration... ✅ (211ms)
  ▶ User Login... ✅ (142ms)
  ▶ Get Current User... ✅ (44ms)
  ▶ Verify Role... ✅ (48ms)
  ▶ Get Sessions... ✅ (44ms)
  ▶ Token Refresh... ✅ (46ms)
  ▶ Logout... ✅ (49ms)
  ▶ Access After Logout... ✅ (43ms)

📋 Role 'teacher': 9 passed, 0 failed

============================================================
📊 Final Test Summary
============================================================

  ✅ STUDENT: 9 passed, 0 failed
      ✅ Health Check: OK (135ms)
      ✅ User Registration: OK (261ms)
      ...

  ✅ TEACHER: 9 passed, 0 failed
      ✅ Health Check: OK (48ms)
      ✅ User Registration: OK (211ms)
      ...

============================================================
Total: 18 passed, 0 failed (1500ms)
============================================================

============================================================
🧹 Cleaning up test data...
============================================================

  Deleting user by ID: 296e3a4b...
    ✅ User 296e3a4b... deleted
  Deleting user by ID: eff66d8d...
    ✅ User eff66d8d... deleted
  Searching for test users with prefix: test_auth_...
    No test users found

✅ Cleanup completed
```
