#!/usr/bin/env python3
"""
Утилита для тестирования SSH туннеля с автоматическим вводом пароля.

Проверяет работу SSH туннеля с использованием переменных окружения.
"""
import sys
import time
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.config import get_settings
from utils.ssh_tunnel import SSHTunnel


def test_ssh_config():
    """Тест конфигурации SSH."""
    print("📋 Проверка конфигурации SSH туннеля...")
    
    try:
        settings = get_settings()
        config = settings.get_ssh_tunnel_config()
        
        print(f"✅ SSH туннель enabled: {config['enabled']}")
        print(f"✅ Локальный порт: {config['local_port']}")
        print(f"✅ Удаленный хост: {config['remote_host']}")
        print(f"✅ SSH ключ: {config['key_path']}")
        
        if config['key_passphrase']:
            print(f"✅ Пароль SSH ключа: настроен ({len(config['key_passphrase'])} символов)")
            return True
        else:
            print(f"❌ Пароль SSH ключа: НЕ настроен")
            print("💡 Добавьте SSH_TUNNEL_KEY_PASSPHRASE в .env.local")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return False


def test_ssh_tunnel():
    """Тест создания SSH туннеля."""
    print("\n🔗 Тестирование создания SSH туннеля...")
    
    tunnel = None
    try:
        tunnel = SSHTunnel()
        
        print("🚀 Создание SSH туннеля с автоматическим вводом пароля...")
        success = tunnel.create_tunnel()
        
        if success:
            print("✅ SSH туннель создан успешно!")
            
            # Проверяем активность туннеля
            if tunnel.is_tunnel_active():
                print("✅ SSH туннель активен")
                
                # Показываем информацию
                info = tunnel.get_tunnel_info()
                print("📋 Информация о туннеле:")
                for key, value in info.items():
                    if key != "ssh_key":
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
    finally:
        if tunnel:
            print("\n🔒 Закрытие туннеля...")
            tunnel.close_tunnel()


def test_postgresql_connection():
    """Тест подключения к PostgreSQL через туннель."""
    print("\n🔍 Тестирование подключения к PostgreSQL...")
    
    tunnel = None
    try:
        # Создаем туннель
        tunnel = SSHTunnel()
        success = tunnel.create_tunnel()
        
        if not success:
            print("❌ Не удалось создать SSH туннель")
            return False
        
        # Ждем установки соединения
        print("⏳ Ожидание установки туннеля (5 секунд)...")
        time.sleep(5)
        
        # Простая проверка подключения
        from utils.data.postgresql_diagnostic import PostgreSQLDiagnostic
        
        async def test_connection():
            try:
                async with PostgreSQLDiagnostic() as diagnostic:
                    config_ok = await diagnostic.check_configuration()
                    connection_ok = await diagnostic.check_connection()
                    
                    if config_ok and connection_ok:
                        print("✅ PostgreSQL подключение работает!")
                        return True
                    else:
                        print("❌ PostgreSQL подключение не работает")
                        return False
            except Exception as e:
                print(f"❌ Ошибка PostgreSQL: {e}")
                return False
        
        import asyncio
        result = asyncio.run(test_connection())
        return result
        
    except Exception as e:
        print(f"❌ Ошибка тестирования PostgreSQL: {e}")
        return False
    finally:
        if tunnel:
            tunnel.close_tunnel()


def main():
    """Основная функция."""
    print("🚀 SSH Tunnel Auto Test")
    print("=" * 50)
    
    # Последовательные тесты
    tests = [
        ("SSH Configuration", test_ssh_config),
        ("SSH Tunnel Creation", test_ssh_tunnel),
        ("PostgreSQL Connection", test_postgresql_connection)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Тест {test_name} failed: {e}")
            results[test_name] = False
    
    # Итоговый отчет
    print(f"\n{'='*60}")
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print(f"{'='*60}")
    
    successful = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"Результат: {successful}/{total} тестов прошли успешно")
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"   {status} {test_name}")
    
    if successful == total:
        print("\n🎉 SSH туннель с автоматическим вводом пароля работает!")
        print("💡 Можете использовать автоматизированное подключение")
    elif successful >= total * 0.5:
        print("\n⚠️ SSH туннель частично работает")
    else:
        print("\n❌ SSH туннель не работает")
        print("🔧 Проверьте настройки SSH_TUNNEL_KEY_PASSPHRASE в .env.local")
    
    return successful == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 