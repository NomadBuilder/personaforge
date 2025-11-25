.PHONY: help install test run clean docker-up docker-down

help:
	@echo "PersonaForge Watcher - Makefile Commands"
	@echo ""
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run tests"
	@echo "  make run        - Run development server"
	@echo "  make docker-up  - Start PostgreSQL with Docker"
	@echo "  make docker-down - Stop PostgreSQL"
	@echo "  make clean      - Clean cache and temp files"

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

run:
	python app.py

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".pytest_cache" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

