# Makefile для автоматизации тестирования RAG Construction Materials API

.PHONY: test-unit test-integration test-functional test-performance test-all test-coverage test-fast test-verbose clean-test

# Переменные
PYTHON := python
PYTEST := pytest
PYTEST_ARGS := -v --tb=short

# Быстрые unit тесты
test-unit:
	@echo "🧪 Запуск unit тестов..."
	$(PYTEST) -m unit $(PYTEST_ARGS)

# Интеграционные тесты
test-integration:
	@echo "🔧 Запуск интеграционных тестов..."
	TEST_MODE=real $(PYTEST) -m integration $(PYTEST_ARGS)

# Функциональные тесты
test-functional:
	@echo "🎯 Запуск функциональных тестов..."
	TEST_MODE=real $(PYTEST) -m functional $(PYTEST_ARGS)

# Тесты производительности
test-performance:
	@echo "⚡ Запуск тестов производительности..."
	$(PYTEST) -m performance $(PYTEST_ARGS)

# Все тесты
test-all:
	@echo "🎪 Запуск всех тестов..."
	$(PYTEST) $(PYTEST_ARGS)

# Тесты с покрытием кода
test-coverage:
	@echo "📊 Запуск тестов с анализом покрытия..."
	$(PYTEST) --cov=. --cov-report=html --cov-report=term --cov-report=xml $(PYTEST_ARGS)

# Только быстрые тесты (исключая slow)
test-fast:
	@echo "🚀 Запуск быстрых тестов..."
	$(PYTEST) -m "not slow" $(PYTEST_ARGS)

# Тесты с детальным выводом
test-verbose:
	@echo "📝 Запуск тестов с детальным выводом..."
	$(PYTEST) -v -s --tb=long

# Очистка тестовых файлов
clean-test:
	@echo "🧹 Очистка тестовых файлов..."
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

# Комбинированные команды
test-quick: clean-test test-unit
	@echo "✅ Быстрые тесты завершены"

test-ci: clean-test test-unit test-integration
	@echo "✅ CI тесты завершены"

test-full: clean-test test-all test-coverage
	@echo "✅ Полный цикл тестирования завершен"

# Проверка зависимостей
check-deps:
	@echo "🔍 Проверка зависимостей для тестирования..."
	$(PYTHON) -m pip check

# Установка зависимостей для тестирования
install-test-deps:
	@echo "📦 Установка зависимостей для тестирования..."
	$(PYTHON) -m pip install -r requirements-dev.txt

# Запуск тестов по файлам
test-file:
	@echo "📄 Запуск тестов из файла: $(FILE)"
	$(PYTEST) $(FILE) $(PYTEST_ARGS)

# Запуск тестов по паттерну
test-pattern:
	@echo "🔍 Запуск тестов по паттерну: $(PATTERN)"
	$(PYTEST) -k "$(PATTERN)" $(PYTEST_ARGS)

# Запуск тестов с профилированием
test-profile:
	@echo "📈 Запуск тестов с профилированием..."
	$(PYTEST) --profile $(PYTEST_ARGS)

# Валидация тестов
test-validate:
	@echo "✅ Валидация тестов..."
	$(PYTEST) --collect-only -q

# Помощь
help:
	@echo "📚 Доступные команды:"
	@echo "  test-unit         - Запуск unit тестов"
	@echo "  test-integration  - Запуск интеграционных тестов"
	@echo "  test-functional   - Запуск функциональных тестов"
	@echo "  test-performance  - Запуск тестов производительности"
	@echo "  test-all          - Запуск всех тестов"
	@echo "  test-coverage     - Тесты с анализом покрытия"
	@echo "  test-fast         - Только быстрые тесты"
	@echo "  test-verbose      - Тесты с детальным выводом"
	@echo "  clean-test        - Очистка тестовых файлов"
	@echo "  test-quick        - Быстрые unit тесты"
	@echo "  test-ci           - Тесты для CI/CD"
	@echo "  test-full         - Полный цикл тестирования"
	@echo "  check-deps        - Проверка зависимостей"
	@echo "  install-test-deps - Установка зависимостей"
	@echo "  test-file FILE=<file> - Тесты из конкретного файла"
	@echo "  test-pattern PATTERN=<pattern> - Тесты по паттерну"
	@echo "  test-profile      - Тесты с профилированием"
	@echo "  test-validate     - Валидация тестов"
	@echo "  help              - Показать эту справку"

# ========================================
# DEPENDENCY MANAGEMENT
# ========================================
.PHONY: install install-dev update-deps check-deps clean-deps

install:
	@echo "📦 Installing production dependencies..."
	pip install -r requirements.txt

install-dev:
	@echo "🔧 Installing development dependencies..."
	pip install -r requirements-dev.txt

install-all:
	@echo "📦 Installing all dependencies with pip-tools..."
	pip install -e .[dev,docs,analysis,database]

update-deps:
	@echo "🔄 Updating dependencies..."
	pip install --upgrade pip setuptools wheel
	pip install --upgrade -r requirements.txt
	pip install --upgrade -r requirements-dev.txt

check-deps:
	@echo "🔍 Checking dependency conflicts..."
	pip check
	@echo "✅ Dependencies check complete"

list-deps:
	@echo "📋 Listing installed packages..."
	pip list --format=columns

outdated-deps:
	@echo "⏰ Checking for outdated packages..."
	pip list --outdated --format=columns

clean-deps:
	@echo "🧹 Cleaning unused packages..."
	pip-autoremove -y || echo "pip-autoremove not installed"

freeze-deps:
	@echo "❄️ Freezing current dependencies..."
	pip freeze > requirements-frozen.txt
	@echo "📄 Frozen dependencies saved to requirements-frozen.txt"

# ========================================
# SECURITY & VULNERABILITY SCANNING
# ========================================
.PHONY: security-scan audit-deps

security-scan:
	@echo "🔒 Running security scan..."
	pip install safety
	safety check
	@echo "✅ Security scan complete"

audit-deps:
	@echo "🔍 Auditing dependencies for vulnerabilities..."
	pip-audit || echo "pip-audit not installed, install with: pip install pip-audit"

# ========================================
# CODE QUALITY
# ========================================
.PHONY: format lint type-check quality

format:
	@echo "🎨 Formatting code with black..."
	black .
	@echo "🔧 Sorting imports with isort..."
	isort .

lint:
	@echo "🔍 Running flake8 linting..."
	flake8 .

type-check:
	@echo "🔬 Running mypy type checking..."
	mypy .

quality: format lint type-check
	@echo "✅ Code quality checks complete"

# ========================================
# TESTING
# ========================================
.PHONY: test test-unit test-integration test-coverage

test:
	@echo "🧪 Running all tests..."
	pytest

test-unit:
	@echo "🧪 Running unit tests..."
	pytest -m "unit" -v

test-integration:
	@echo "🧪 Running integration tests..."
	pytest -m "integration" -v

test-coverage:
	@echo "📊 Running tests with coverage..."
	pytest --cov=. --cov-report=html --cov-report=term-missing

# ========================================
# DEVELOPMENT HELPERS
# ========================================
.PHONY: dev-setup pre-commit-install dev-server

dev-setup: install-dev pre-commit-install
	@echo "🚀 Development environment setup complete!"

pre-commit-install:
	@echo "🪝 Installing pre-commit hooks..."
	pre-commit install

dev-server:
	@echo "🚀 Starting development server with auto-reload..."
	uvicorn main:app --reload --host 0.0.0.0 --port 8000 