#!/usr/bin/env python3
"""
Тест интеграции SSH туннеля с проектом.

Простой тест для проверки автоматизированного запуска SSH туннеля 
с использованием переменных окружения.
"""
import asyncio
import sys
import os
import time
from pathlib import Path
from typing import Optional

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.config import get_settings
from utils.ssh_tunnel import SSHTunnel
from utils.data.postgresql_diagnostic import PostgreSQLDiagnostic

class SSHTunnelIntegrationTest:
    """Тест интеграции SSH туннеля."""
    
    def __init__(self):
        """Инициализация теста."""
        self.settings = get_settings()
        self.tunnel: Optional[SSHTunnel] = None
        
    def print_header(self, title: str):
        """Печать заголовка."""
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}")
    
    def print_step(self, step: str):
        """Печать шага."""
        print(f"\n📋 {step}")
        print("-" * 40)
    
    def test_ssh_configuration(self) -> bool:
        """Тест конфигурации SSH туннеля."""
        self.print_step("SSH Tunnel Configuration Test")
        
        try:
            config = self.settings.get_ssh_tunnel_config()
            
            print(f"✅ SSH туннель enabled: {config['enabled']}")
            print(f"✅ Локальный порт: {config['local_port']}")
            print(f"✅ Удаленный хост: {config['remote_host']}")
            print(f"✅ Пользователь: {config['remote_user']}")
            print(f"✅ SSH ключ: {config['key_path']}")
            
            # Проверяем наличие пароля (не показываем его)
            if config['key_passphrase']:
                print(f"✅ Пароль SSH ключа: настроен ({len(config['key_passphrase'])} символов)")
            else:
                print(f"⚠️ Пароль SSH ключа: не настроен")
            
            # Проверяем существование SSH ключа
            key_path = Path(config['key_path']).expanduser()
            if key_path.exists():
                print(f"✅ SSH ключ найден: {key_path}")
            else:
                print(f"❌ SSH ключ не найден: {key_path}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка конфигурации SSH: {e}")
            return False
    
    def test_tunnel_creation(self) -> bool:
        """Тест создания SSH туннеля."""
        self.print_step("SSH Tunnel Creation Test")
        
        try:
            self.tunnel = SSHTunnel()
            
            print("🔗 Создание SSH туннеля...")
            success = self.tunnel.create_tunnel()
            
            if success:
                print("✅ SSH туннель создан успешно")
                
                # Проверяем статус туннеля
                if self.tunnel.is_tunnel_active():
                    print("✅ SSH туннель активен")
                    
                    # Показываем информацию о туннеле
                    info = self.tunnel.get_tunnel_info()
                    print("📋 Информация о туннеле:")
                    for key, value in info.items():
                        if key != "ssh_key":  # Не показываем путь к ключу
                            print(f"   {key}: {value}")
                    
                    return True
                else:
                    print("❌ SSH туннель не активен")
                    return False
            else:
                print("❌ Не удалось создать SSH туннель")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка создания туннеля: {e}")
            return False
    
    async def test_postgresql_connection(self) -> bool:
        """Тест подключения к PostgreSQL через туннель."""
        self.print_step("PostgreSQL Connection Test")
        
        try:
            # Даем туннелю время для полной инициализации
            print("⏳ Ожидание инициализации туннеля...")
            time.sleep(5)
            
            async with PostgreSQLDiagnostic() as diagnostic:
                print("🔍 Тестирование подключения к PostgreSQL...")
                
                # Проверяем только основные функции
                config_ok = await diagnostic.check_configuration()
                connection_ok = await diagnostic.check_connection()
                
                if config_ok and connection_ok:
                    print("✅ PostgreSQL подключение через SSH туннель работает!")
                    
                    # Дополнительная проверка - выполнение простого запроса
                    try:
                        query = "SELECT current_database(), current_user, version()"
                        result = await diagnostic.adapter.execute_query(query)
                        if result:
                            row = result[0]
                            print(f"📊 База данных: {row.get('current_database', 'N/A')}")
                            print(f"📊 Пользователь: {row.get('current_user', 'N/A')}")
                            postgres_version = row.get('version', 'N/A')
                            if postgres_version != 'N/A':
                                # Показываем только первую часть версии
                                version_short = postgres_version.split(',')[0] if ',' in postgres_version else postgres_version
                                print(f"📊 Версия: {version_short}")
                    except Exception as e:
                        print(f"⚠️ Дополнительная проверка не удалась: {e}")
                    
                    return True
                else:
                    print("❌ PostgreSQL подключение не работает")
                    return False
                    
        except Exception as e:
            print(f"❌ Ошибка тестирования PostgreSQL: {e}")
            return False
    
    def cleanup_tunnel(self):
        """Очистка SSH туннеля."""
        if self.tunnel:
            try:
                print("\n🔒 Закрытие SSH туннеля...")
                self.tunnel.close_tunnel()
                print("✅ SSH туннель закрыт")
            except Exception as e:
                print(f"⚠️ Ошибка закрытия туннеля: {e}")
    
    async def run_full_test(self) -> bool:
        """Запуск полного теста интеграции."""
        self.print_header("SSH Tunnel Integration Test")
        
        try:
            # Последовательно запускаем тесты
            tests = [
                ("Configuration", self.test_ssh_configuration),
                ("Tunnel Creation", self.test_tunnel_creation),
                ("PostgreSQL Connection", self.test_postgresql_connection)
            ]
            
            results = {}
            
            for test_name, test_func in tests:
                try:
                    if asyncio.iscoroutinefunction(test_func):
                        result = await test_func()
                    else:
                        result = test_func()
                    results[test_name] = result
                except Exception as e:
                    print(f"❌ Тест {test_name} failed: {e}")
                    results[test_name] = False
            
            # Выводим итоговый отчет
            self.print_step("Integration Test Summary")
            
            successful = sum(1 for result in results.values() if result)
            total = len(results)
            
            print(f"📊 Результат: {successful}/{total} тестов прошли успешно")
            
            for test_name, result in results.items():
                status = "✅" if result else "❌"
                print(f"   {status} {test_name}")
            
            if successful == total:
                print("\n🎉 SSH туннель полностью интегрирован с проектом!")
                print("💡 Теперь можно запускать приложение с автоматическим SSH туннелем")
                return True
            elif successful >= total * 0.5:
                print("\n⚠️ SSH туннель частично работает, есть проблемы")
                return False
            else:
                print("\n❌ SSH туннель не работает, требуется настройка")
                return False
                
        finally:
            # Всегда закрываем туннель
            self.cleanup_tunnel()


async def main():
    """Основная функция для запуска теста."""
    test = SSHTunnelIntegrationTest()
    success = await test.run_full_test()
    
    if success:
        print("\n💡 Следующие шаги:")
        print("   1. Добавьте пароль SSH ключа в .env.local:")
        print("      SSH_TUNNEL_KEY_PASSPHRASE=your_actual_passphrase")
        print("   2. Запустите приложение: python main.py")
        print("   3. SSH туннель будет запускаться автоматически")
        sys.exit(0)
    else:
        print("\n🔧 Требуется дополнительная настройка:")
        print("   1. Проверьте SSH ключ и пароль")
        print("   2. Убедитесь, что сервер доступен")
        print("   3. Проверьте настройки в .env.local")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 