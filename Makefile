# Retirement Optimization Project - Test Suite
# ============================================

.PHONY: test test-backend test-frontend test-functional

# Run all tests
test: test-backend test-frontend test-functional
	@echo "All tests completed!"

# Backend unit + integration tests
test-backend:
	cd backend && ../.venv/bin/python -m pytest tests -v
	cd backend && ../.venv/bin/python manage.py test api -v2

# Frontend unit tests
test-frontend:
	cd frontend && npm run test:run

# Functional / E2E tests (builds frontend, starts server, runs Playwright)
test-functional:
	.venv/bin/python -m pytest functional_tests -v -m e2e
