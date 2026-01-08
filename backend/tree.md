📁 專案結構
============

backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 應用入口
│   ├── config.py               # 環境配置
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py         # JWT & Cookie 處理
│   │   ├── dependencies.py     # 依賴注入
│   │   └── exceptions.py       # 自定義例外
│   │
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── auth_middleware.py  # 認證中間件
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── supabase_service.py # Supabase 服務
│   │   ├── session_service.py  # Session 管理
│   │   ├── redis_service.py    # Redis 快取
│   │   └── auth_service.py     # 認證服務
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py       # API 路由彙整
│   │       ├── auth.py         # 認證 API
│   │       ├── users.py        # 用戶 API
│   │       └── health.py       # 健康檢查
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py             # 用戶模型
│   │   └── session.py          # Session 模型
│   │
│   └── schemas/
│       ├── __init__.py
│       ├── auth.py             # 認證 Schema
│       ├── user.py             # 用戶 Schema
│       └── response.py         # 通用回應 Schema
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_auth.py
│
├── .env.example
├── .env
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md