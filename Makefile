# Makefile for Python Beep Detection API - Clean Version

.PHONY: help install run test clean lint format deploy docs

# Configuration
PYTHON := python3
PIP := pip3
SERVER_URL := http://localhost:8000
TEST_FILE := test_audio.mp3

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Default target
help:
	@echo "$(BLUE)Available commands:$(NC)"
	@echo "  $(GREEN)install$(NC)     - Install dependencies"
	@echo "  $(GREEN)run$(NC)         - Start development server"
	@echo "  $(GREEN)run-api$(NC)     - Start API server (Vercel compatible)"
	@echo "  $(GREEN)test$(NC)        - Run tests"
	@echo "  $(GREEN)clean$(NC)       - Clean up temporary files"
	@echo "  $(GREEN)lint$(NC)        - Run linting"
	@echo "  $(GREEN)format$(NC)      - Format code"
	@echo "  $(GREEN)deploy$(NC)      - Deploy to git"
	@echo "  $(GREEN)docs$(NC)        - Open API documentation"
	@echo ""
	@echo "$(BLUE)Requirements Management:$(NC)"
	@echo "  $(GREEN)use-lightweight$(NC) - Switch to lightweight requirements"
	@echo "  $(GREEN)use-full$(NC)         - Switch to full requirements"
	@echo ""
	@echo "$(BLUE)Quick Tests (using CLI):$(NC)"
	@echo "  $(GREEN)test-health$(NC)       - Test health endpoint"
	@echo "  $(GREEN)test-cross$(NC)        - Test cross-correlation endpoint"
	@echo "  $(GREEN)test-all$(NC)          - Test all endpoints and compare"

# Installation
install:
	@echo "$(YELLOW)Installing dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements.vercel.txt

# Server management
run:
	@echo "$(GREEN)Starting development server...$(NC)"
	uvicorn main:app --host 0.0.0.0 --port 8000 --reload

run-api:
	@echo "$(GREEN)Starting API server...$(NC)"
	uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

kill-server:
	@echo "$(YELLOW)Stopping server...$(NC)"
	pkill -f "uvicorn" || echo "No uvicorn processes found"

# Testing
test:
	@echo "$(YELLOW)Running tests...$(NC)"
	$(PYTHON) -m pytest tests/ -v --tb=short

# Generate test files
generate-tests:
	@echo "$(YELLOW)Generating test audio files...$(NC)"
	$(PYTHON) scripts/generate_test_files.py

# Quick tests using CLI tool
test-health:
	@echo "$(YELLOW)Testing health endpoint...$(NC)"
	$(PYTHON) scripts/test_cli.py --endpoint health

test-cross:
	@echo "$(YELLOW)Testing cross-correlation endpoint...$(NC)"
	if [ -f "$(TEST_FILE)" ]; then \
		$(PYTHON) scripts/test_cli.py --file $(TEST_FILE) --endpoint cross-correlation; \
	else \
		echo "❌ No $(TEST_FILE) found. Please add a test audio file."; \
	fi

test-all:
	@echo "$(YELLOW)Testing all endpoints...$(NC)"
	if [ -f "$(TEST_FILE)" ]; then \
		$(PYTHON) scripts/test_cli.py --file $(TEST_FILE) --endpoint all --compare; \
	else \
		echo "❌ No $(TEST_FILE) found. Please add a test audio file."; \
	fi

# Code quality
lint:
	@echo "$(YELLOW)Running linting...$(NC)"
	flake8 api/ main.py
	mypy api/ main.py --ignore-missing-imports

format:
	@echo "$(YELLOW)Formatting code...$(NC)"
	black api/ main.py
	isort api/ main.py

# Cleanup
clean:
	@echo "$(YELLOW)Cleaning up...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ *.log .coverage htmlcov/

# Requirements management
use-lightweight:
	@echo "$(YELLOW)Switching to lightweight requirements...$(NC)"
	cp requirements.lightweight.txt requirements.vercel.txt
	@echo "$(GREEN)✅ Now using lightweight requirements for Vercel deployment$(NC)"

use-full:
	@echo "$(YELLOW)Switching to full requirements...$(NC)"
	cp requirements.txt requirements.vercel.txt
	@echo "$(GREEN)✅ Now using full requirements for local development$(NC)"

# Deployment
deploy:
	@echo "$(YELLOW)Deploying to git...$(NC)"
	git add .
	git commit -m "Update: $(shell date '+%Y-%m-%d %H:%M:%S')"
	git push origin master

vercel-deploy:
	@echo "$(YELLOW)Deploying to Vercel...$(NC)"
	vercel --prod

# Documentation
docs:
	@echo "$(BLUE)Opening API documentation...$(NC)"
	@echo "$(GREEN)Make sure the server is running first: make run$(NC)"
	@open http://localhost:8000/docs || echo "Server not running"

# Status
status:
	@echo "$(BLUE)=== Project Status ===$(NC)"
	@echo "$(YELLOW)Git status:$(NC)"
	@git status --porcelain
	@echo ""
	@echo "$(YELLOW)Files:$(NC)"
	@echo "Python files: $$(find . -name "*.py" | wc -l)"
	@echo "Audio files: $$(find . -name "*.wav" -o -name "*.mp3" | wc -l)"
	@echo ""
	@echo "$(YELLOW)Requirements:$(NC)"
	@ls -la requirements*.txt

# Development setup
dev-setup: install
	@echo "$(GREEN)✅ Development environment setup complete!$(NC)"
	@echo "Run '$(GREEN)make run$(NC)' to start the server"

# Quick CLI help
cli-help:
	@echo "$(BLUE)CLI Tool Usage:$(NC)"
	@echo "  $(PYTHON) scripts/test_cli.py --file <audio_file> [options]"
	@echo ""
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  $(PYTHON) scripts/test_cli.py --file test.mp3 --endpoint cross-correlation"
	@echo "  $(PYTHON) scripts/test_cli.py --file test.mp3 --endpoint all --compare"
	@echo "  $(PYTHON) scripts/test_cli.py --file test.mp3 --threshold 0.7"