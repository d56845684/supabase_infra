#!/bin/bash

set -e

echo "🧪 開始執行測試..."

# 確認虛擬環境
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  建議在虛擬環境中執行測試"
fi

# 安裝測試依賴
echo "📦 安裝測試依賴..."
pip install -r requirements-test.txt -q

# 執行測試
echo "🔬 執行單元測試..."
pytest tests/unit/ -v --tb=short

echo "🔗 執行整合測試..."
pytest tests/integration/ -v --tb=short

echo "🌐 執行端對端測試..."
pytest tests/e2e/ -v --tb=short

# 產生覆蓋率報告
echo "📊 產生覆蓋率報告..."
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

echo "✅ 測試完成！覆蓋率報告位於 htmlcov/index.html"