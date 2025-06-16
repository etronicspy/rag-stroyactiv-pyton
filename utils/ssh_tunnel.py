#!/usr/bin/env python3
"""
SSH туннель для подключения к удаленной PostgreSQL базе данных
"""
import subprocess
import time
import signal
import sys
import os
from pathlib import Path

class SSHTunnel:
    def __init__(self):
        self.ssh_key_path = Path.home() / ".ssh" / "postgres_key"
        self.local_port = 5435
        self.remote_host = "31.130.148.200"
        self.remote_user = "root"
        self.remote_port = 5432
        self.process = None
        
    def create_tunnel(self):
        """Создает SSH туннель"""
        print(f"🔗 Создание SSH туннеля...")
        print(f"   Локальный порт: {self.local_port}")
        print(f"   Удаленный сервер: {self.remote_user}@{self.remote_host}")
        print(f"   SSH ключ: {self.ssh_key_path}")
        
        # Проверяем существование SSH ключа
        if not self.ssh_key_path.exists():
            print(f"❌ SSH ключ не найден: {self.ssh_key_path}")
            print("💡 Создайте SSH ключ командой: ssh-keygen -t ed25519 -f ~/.ssh/postgres_key")
            return False
        
        # Команда для создания SSH туннеля
        ssh_command = [
            "ssh",
            "-i", str(self.ssh_key_path),
            "-L", f"{self.local_port}:localhost:{self.remote_port}",
            "-N",  # Не выполнять команды на удаленном сервере
            "-T",  # Отключить псевдо-терминал
            f"{self.remote_user}@{self.remote_host}"
        ]
        
        try:
            print(f"🚀 Запуск SSH туннеля...")
            print(f"   Команда: {' '.join(ssh_command)}")
            
            self.process = subprocess.Popen(
                ssh_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Ждем немного для установки соединения
            time.sleep(2)
            
            # Проверяем статус процесса
            poll = self.process.poll()
            if poll is None:
                print("✅ SSH туннель успешно создан!")
                print(f"🔗 PostgreSQL доступен через localhost:{self.local_port}")
                return True
            else:
                stdout, stderr = self.process.communicate()
                print(f"❌ Ошибка создания SSH туннеля:")
                if stderr:
                    print(f"   Stderr: {stderr.decode()}")
                if stdout:
                    print(f"   Stdout: {stdout.decode()}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение при создании SSH туннеля: {e}")
            return False
    
    def close_tunnel(self):
        """Закрывает SSH туннель"""
        if self.process:
            print("🔒 Закрытие SSH туннеля...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
                print("✅ SSH туннель закрыт")
            except subprocess.TimeoutExpired:
                print("⚠️ Принудительное завершение SSH туннеля...")
                self.process.kill()
                self.process.wait()
                print("✅ SSH туннель принудительно закрыт")
            self.process = None
    
    def is_tunnel_active(self):
        """Проверяет активность SSH туннеля"""
        if self.process:
            return self.process.poll() is None
        return False
    
    def get_tunnel_info(self):
        """Возвращает информацию о туннеле"""
        return {
            "local_port": self.local_port,
            "remote_host": self.remote_host,
            "remote_user": self.remote_user,
            "remote_port": self.remote_port,
            "ssh_key": str(self.ssh_key_path),
            "is_active": self.is_tunnel_active()
        }

def signal_handler(sig, frame):
    """Обработчик сигналов для корректного завершения"""
    print("\n🛑 Получен сигнал завершения...")
    if hasattr(signal_handler, 'tunnel'):
        signal_handler.tunnel.close_tunnel()
    sys.exit(0)

def main():
    """Основная функция для создания и поддержания SSH туннеля"""
    print("🚀 SSH Tunnel Manager для PostgreSQL")
    print("=" * 50)
    
    tunnel = SSHTunnel()
    signal_handler.tunnel = tunnel
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Создаем туннель
    if tunnel.create_tunnel():
        print("\n📋 Информация о туннеле:")
        info = tunnel.get_tunnel_info()
        for key, value in info.items():
            print(f"   {key}: {value}")
        
        print("\n💡 Теперь вы можете подключиться к PostgreSQL:")
        print(f"   psql -h localhost -p {tunnel.local_port} -U superadmin -d materials")
        print("\n💡 Или запустить тест подключения:")
        print("   python utils/data/test_postgresql_connection.py")
        print("\n⚠️ Для остановки туннеля нажмите Ctrl+C")
        
        try:
            # Поддерживаем туннель активным
            while tunnel.is_tunnel_active():
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Получен Ctrl+C...")
        finally:
            tunnel.close_tunnel()
    else:
        print("❌ Не удалось создать SSH туннель")
        print("\n💡 Возможные причины:")
        print("   1. SSH ключ не скопирован на удаленный сервер")
        print("   2. Неверные учетные данные SSH")
        print("   3. Сервер недоступен")
        print("   4. Порт уже занят")
        print("\n🔧 Для копирования SSH ключа на сервер:")
        print("   ssh-copy-id -i ~/.ssh/postgres_key root@31.130.148.200")
        sys.exit(1)

if __name__ == "__main__":
    main() 