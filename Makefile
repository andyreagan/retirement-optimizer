# Retirement Optimization Project - Test Suite
# ============================================

.PHONY: test test-backend test-frontend test-e2e

# Run all tests (backend + frontend + e2e)
test: test-backend test-frontend test-e2e
	@echo "All tests completed!"

# Backend unit/integration tests
test-backend:
	cd backend && uv run --group test pytest tests/ -v
	cd backend && uv run --group test python manage.py test

# Frontend unit tests
test-frontend:
	cd frontend && npm run test:run

# End-to-end tests (starts its own server via subprocess)
test-e2e:
	./build_frontend.sh
	uv run --group test pytest functional_tests/ -v --timeout=120
