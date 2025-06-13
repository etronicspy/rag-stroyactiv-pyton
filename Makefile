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