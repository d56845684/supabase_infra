tests/
├── conftest.py              # 共用 fixtures
├── unit/
│   ├── test_security.py     # 安全模組單元測試
│   └── test_session_service.py  # Session 服務單元測試
├── integration/
│   ├── test_auth_api.py     # 認證 API 整合測試
│   ├── test_user_api.py     # 用戶 API 整合測試
│   ├── test_health_api.py   # 健康檢查 API 測試
│   └── test_middleware.py   # 中間件測試
└── e2e/
    ├── test_auth_flow.py    # 認證流程端對端測試
    └── test_permission_flow.py  # 權限流程端對端測試