.PHONY: test test-unit test-integration test-e2e test-cov

# 執行所有測試
test:
	pytest tests/ -v

# 只執行單元測試
test-unit:
	pytest tests/unit/ -v -m unit

# 只執行整合測試
test-integration:
	pytest tests/integration/ -v -m integration

# 只執行端對端測試
test-e2e:
	pytest tests/e2e/ -v -m e2e

# 執行測試並產生覆蓋率報告
test-cov:
	pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

# 執行測試 (快速模式，跳過慢測試)
test-fast:
	pytest tests/ -v -m "not slow"

# 執行特定測試檔案
test-file:
	pytest $(FILE) -v

# 清除測試快取
test-clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage