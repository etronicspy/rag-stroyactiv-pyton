#!/usr/bin/env python3
"""
Утилита для запуска тестов утилит с различными режимами
"""

import sys
import subprocess
import argparse
from pathlib import Path
import os


def run_unit_tests():
    """Запуск только unit тестов (без интеграционных)"""
    print("🧪 Запуск Unit тестов утилит...")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/utils/",
        "-v", 
        "--tb=short",
        "-m", "not integration",
        "--color=yes"
    ]
    
    return subprocess.run(cmd, cwd=Path(__file__).parent.parent.parent)


def run_integration_tests():
    """Запуск только интеграционных тестов"""
    print("🔗 Запуск интеграционных тестов утилит...")
    
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/utils/",
        "-v",
        "--tb=short", 
        "-m", "integration",
        "--color=yes"
    ]
    
    return subprocess.run(cmd, cwd=Path(__file__).parent.parent.parent)


def run_all_tests():
    """Запуск всех тестов утилит"""
    print("🚀 Запуск всех тестов утилит...")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/utils/",
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    return subprocess.run(cmd, cwd=Path(__file__).parent.parent.parent)


def run_specific_test(test_name):
    """Запуск конкретного теста"""
    print(f"🎯 Запуск теста: {test_name}")
    
    cmd = [
        sys.executable, "-m", "pytest",
        f"tests/utils/{test_name}",
        "-v",
        "--tb=short", 
        "--color=yes"
    ]
    
    return subprocess.run(cmd, cwd=Path(__file__).parent.parent.parent)


def run_with_coverage():
    """Запуск тестов с анализом покрытия кода"""
    print("📊 Запуск тестов с анализом покрытия...")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/utils/",
        "--cov=utils",
        "--cov-report=html",
        "--cov-report=term-missing",
        "-v",
        "--color=yes"
    ]
    
    return subprocess.run(cmd, cwd=Path(__file__).parent.parent.parent)


def check_environment():
    """Проверка окружения для тестов"""
    print("🔍 Проверка окружения для тестов...")
    
    # Проверяем наличие pytest
    try:
        import pytest
        print(f"✅ pytest установлен: {pytest.__version__}")
    except ImportError:
        print("❌ pytest не установлен")
        return False
    
    # Проверяем наличие coverage
    try:
        import coverage
        print(f"✅ coverage установлен: {coverage.__version__}")
    except ImportError:
        print("⚠️  coverage не установлен (опционально)")
    
    # Проверяем переменные окружения
    env_vars = ['OPENAI_API_KEY', 'QDRANT_URL', 'QDRANT_API_KEY']
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * (len(value) - 4) + value[-4:]}")
        else:
            print(f"⚠️  {var}: не установлена")
    
    # Проверяем доступность сервисов
    try:
        import requests
        
        # Проверяем API
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            print(f"✅ API сервер доступен: {response.status_code}")
        except Exception:
            print("❌ API сервер недоступен")
        
        # Проверяем Qdrant
        try:
            response = requests.get("http://localhost:6333", timeout=2)
            print(f"✅ Qdrant доступен: {response.status_code}")
        except Exception:
            print("❌ Qdrant недоступен")
            
    except ImportError:
        print("⚠️  requests не установлен для проверки сервисов")
    
    return True


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description="Запуск тестов утилит")
    parser.add_argument(
        "mode",
        choices=["unit", "integration", "all", "coverage", "check"],
        help="Режим запуска тестов"
    )
    parser.add_argument(
        "--test",
        help="Запуск конкретного теста (например: test_load_materials.py)"
    )
    
    args = parser.parse_args()
    
    # Проверяем окружение
    if args.mode == "check":
        check_environment()
        return
    
    # Запуск конкретного теста
    if args.test:
        result = run_specific_test(args.test)
        sys.exit(result.returncode)
    
    # Запуск по режиму
    if args.mode == "unit":
        result = run_unit_tests()
    elif args.mode == "integration":
        result = run_integration_tests()
    elif args.mode == "all":
        result = run_all_tests()
    elif args.mode == "coverage":
        result = run_with_coverage()
    else:
        print(f"❌ Неизвестный режим: {args.mode}")
        sys.exit(1)
    
    # Выводим результат
    if result.returncode == 0:
        print("✅ Все тесты прошли успешно!")
    else:
        print("❌ Некоторые тесты завершились с ошибками")
    
    sys.exit(result.returncode)


if __name__ == "__main__":
    main() 