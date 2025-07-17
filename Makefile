# Retirement Optimization Project - Test Suite
# ============================================

# Python and Node paths
PYTHON := python
NPM := npm
PYTEST := pytest
MANAGE := backend/manage.py

# Test directories
TEST_DIR := tests
BACKEND_DIR := backend
FRONTEND_DIR := frontend

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

.PHONY: help test test-backend test-frontend test-functional clean-test install-test-deps

help:
	@echo "$(GREEN)Retirement Optimization Test Suite$(NC)"
	@echo "=================================="
	@echo "Available commands:"
	@echo "  $(YELLOW)make test$(NC)              - Run all tests"
	@echo "  $(YELLOW)make test-backend$(NC)      - Run backend tests"
	@echo "  $(YELLOW)make test-frontend$(NC)     - Run frontend tests"
	@echo "  $(YELLOW)make test-functional$(NC)   - Run functional tests"
	@echo ""
	@echo "  $(YELLOW)make clean-test$(NC)        - Clean test artifacts"
	@echo "  $(YELLOW)make install-test-deps$(NC) - Install test dependencies"

# Install test dependencies
install-test-deps:
	@echo "$(GREEN)Installing test dependencies...$(NC)"
	cd $(BACKEND_DIR) && pip install -r ../requirements-test.txt
	cd $(FRONTEND_DIR) && npm install --save-dev
	@echo "$(GREEN)Installing additional test tools...$(NC)"
	pip install pytest-django pytest-xdist pytest-timeout
	@echo "$(GREEN)Dependencies installed!$(NC)"

# Run all tests
test: test-backend test-frontend test-functional
	@echo "$(GREEN)All tests completed!$(NC)"

# Backend tests
test-backend:
	@echo "$(YELLOW)Running backend tests...$(NC)"
	cd $(BACKEND_DIR) && $(PYTEST) ../$(TEST_DIR)/backend/ -v --tb=short
	@echo "$(YELLOW)Running Django app tests...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) $(MANAGE) test api payments

# Frontend tests
test-frontend:
	@echo "$(YELLOW)Running frontend tests...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) run test:run

# Functional tests
test-functional:
	@echo "$(YELLOW)Running functional tests...$(NC)"
	@echo "$(YELLOW)Starting backend server...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) $(MANAGE) runserver --noreload &
	@sleep 3
	@echo "$(YELLOW)Starting frontend server...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) run dev -- --port 5173 &
	@sleep 5
	@echo "$(YELLOW)Running functional tests...$(NC)"
	cd $(BACKEND_DIR) && $(PYTEST) ../$(TEST_DIR)/functional/ -v --tb=short || (pkill -f "manage.py runserver" && pkill -f "vite" && exit 1)
	@pkill -f "manage.py runserver" || true
	@pkill -f "vite" || true
	@echo "$(GREEN)Functional tests completed!$(NC)"

# Clean test artifacts
clean-test:
	@echo "$(YELLOW)Cleaning test artifacts...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)Test artifacts cleaned!$(NC)"