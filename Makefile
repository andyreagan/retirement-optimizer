# Retirement Optimization Project - Test Suite
# ============================================

# Test directories
.PHONY: test test-backend test-frontend test-functional

# Run all tests
test: test-backend test-frontend test-functional
	@echo "All tests completed!"

# Backend tests
test-backend:
	cd backend && pytest tests
	cd backend && python manage.py test

# Frontend tests
test-frontend:
	cd frontend && npm run test:run

# Functional tests
test-functional:
	./build_frontend.sh 
	cd backend && python manage.py runserver &
	@sleep 3
	pytest functional_tests
	@pkill -f "manage.py runserver" || true
