# Retirement Optimization Project - Test Suite
# ============================================

.PHONY: test test-backend test-frontend test-functional

# Run all tests (backend + frontend + functional)
test: test-backend test-frontend test-functional
	@echo "All tests completed!"

# Backend unit/integration tests
test-backend:
	cd backend && uv run --group test pytest tests/ -v
	cd backend && uv run --group test python manage.py test

# Frontend unit tests
test-frontend:
	cd frontend && npm run test:run

# Functional/E2E tests (starts its own server via subprocess)
test-functional:
	./build_frontend.sh
	uv run --group test pytest functional_tests/ -v --timeout=120
