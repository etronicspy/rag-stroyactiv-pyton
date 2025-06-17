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

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import get_settings

class SSHTunnel:
    def __init__(self):
        # Загружаем настройки из конфигурации
        try:
            self.settings = get_settings()
            self.config = self.settings.get_ssh_tunnel_config()
            
            # Настройки из конфигурации
            self.key_path = Path(self.config["key_path"]).expanduser()
            self.local_port = self.config["local_port"]
            self.remote_host = self.config["remote_host"]
            self.remote_user = self.config["remote_user"]
            self.remote_port = self.config["remote_port"]
            self.key_passphrase = self.config["key_passphrase"]
            self.timeout = self.config["timeout"]
            self.compression = self.config["compression"]
            self.keep_alive = self.config["keep_alive"]
            self.strict_host_key_checking = self.config["strict_host_key_checking"]
            
        except Exception as e:
            print(f"⚠️ Ошибка загрузки конфигурации: {e}")
            print("🔧 Используем настройки по умолчанию...")
            
            # Fallback к настройкам по умолчанию
            self.key_path = Path.home() / ".ssh" / "postgres_key"
            self.local_port = 5435
            self.remote_host = "31.130.148.200"
            self.remote_user = "root"
            self.remote_port = 5432
            self.key_passphrase = None
            self.timeout = 30
            self.compression = True
            self.keep_alive = 60
            self.strict_host_key_checking = False
        
        self.process = None
        self.pexpect_process = None
        self.askpass_file = None
        
    def create_tunnel(self):
        """Создает SSH туннель"""
        print("🔗 Создание SSH туннеля...")
        print(f"   Локальный порт: {self.local_port}")
        print(f"   Удаленный сервер: {self.remote_user}@{self.remote_host}")
        print(f"   SSH ключ: {self.key_path}")
        
        # Базовая команда SSH
        ssh_command = [
            "ssh",
            "-i", str(self.key_path),
            "-L", f"{self.local_port}:localhost:{self.remote_port}",
            "-N",  # Не выполнять команду, только порт форвардинг
            "-T",  # Отключить TTY allocation
            "-C",  # Включить сжатие
            "-o", "StrictHostKeyChecking=no",
            "-o", "ServerAliveInterval=60",
            "-o", "ServerAliveCountMax=3"
        ]
        
        if self.timeout > 0:
            ssh_command.extend(["-o", f"ConnectTimeout={self.timeout}"])
        
        # Добавляем хост в конце
        ssh_command.append(f"{self.remote_user}@{self.remote_host}")
        
        try:
            print(f"🚀 Запуск SSH туннеля...")
            print(f"   Команда: {' '.join(ssh_command)}")
            
            # Настройка окружения для автоматического ввода пароля
            env = os.environ.copy()
            
            # Если есть пароль, используем pexpect для автоматического ввода
            if self.key_passphrase:
                print("🔐 Используется автоматический ввод пароля SSH ключа из переменных окружения")
                
                try:
                    import pexpect
                    
                    print(f"🚀 Запуск SSH с автоматическим вводом пароля через pexpect...")
                    
                    # Запускаем SSH с pexpect для автоматического ввода пароля
                    ssh_command_str = ' '.join(ssh_command)
                    print(f"   Команда: {ssh_command_str}")
                    
                    # Устанавливаем переменные окружения для pexpect
                    pexpect_env = env.copy()
                    
                    # Создаем процесс с pexpect
                    self.pexpect_process = pexpect.spawn(
                        ssh_command_str,
                        env=pexpect_env,
                        timeout=30
                    )
                    
                    # Ожидаем запрос пароля и автоматически вводим его
                    try:
                        index = self.pexpect_process.expect([
                            'Enter passphrase for key',
                            'password:',
                            pexpect.TIMEOUT,
                            pexpect.EOF
                        ], timeout=10)
                        
                        if index == 0 or index == 1:
                            # Вводим пароль
                            self.pexpect_process.sendline(self.key_passphrase)
                            print("✅ Пароль SSH ключа введен автоматически")
                            
                            # Ожидаем завершения установки соединения
                            self.pexpect_process.expect(pexpect.TIMEOUT, timeout=3)
                            
                        elif index == 2:
                            print("⚠️ Timeout при ожидании запроса пароля")
                        elif index == 3:
                            print("⚠️ SSH процесс завершился неожиданно")
                            
                    except pexpect.exceptions.TIMEOUT:
                        # Это нормально для SSH туннеля - он должен работать в фоне
                        pass
                    except pexpect.exceptions.EOF:
                        print("⚠️ SSH процесс завершился")
                    
                    # Проверяем, что процесс еще активен
                    if self.pexpect_process.isalive():
                        print("✅ SSH туннель успешно создан с автоматическим вводом пароля!")
                        # Сохраняем ссылку на pexpect процесс
                        self.process = self.pexpect_process
                        print(f"🔗 PostgreSQL доступен через localhost:{self.local_port}")
                        return True
                    else:
                        print("❌ SSH туннель не смог установиться")
                        self.pexpect_process = None
                        return False
                        
                except ImportError:
                    print("⚠️ pexpect не установлен, используем fallback метод")
                    # Fallback к старому методу с askpass
                    return self._create_tunnel_with_askpass(ssh_command, env)
                except Exception as e:
                    print(f"❌ Ошибка при использовании pexpect: {e}")
                    return False
            else:
                print("⚠️ Пароль SSH ключа не задан в переменных окружения")
                print("💡 Добавьте SSH_TUNNEL_KEY_PASSPHRASE в .env.local для автоматизации")
                
                # Обычный запуск без автоматического ввода пароля
                self.process = subprocess.Popen(
                    ssh_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env
                )
                
                # Ждем немного для установки соединения
                time.sleep(3)
                
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
            
    def _create_tunnel_with_askpass(self, ssh_command, env):
        """Fallback метод с использованием SSH_ASKPASS"""
        import tempfile
        import stat
        
        print("🔐 Использование fallback метода с SSH_ASKPASS")
        
        # Создаем askpass скрипт
        askpass_script = f"""#!/bin/bash
echo '{self.key_passphrase}'
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(askpass_script)
            askpass_file = f.name
        
        try:
            # Делаем скрипт исполнимым
            os.chmod(askpass_file, stat.S_IRWXU)
            
            # Настраиваем окружение для SSH
            env["SSH_ASKPASS"] = askpass_file
            env["DISPLAY"] = ":0"
            
            print(f"🔑 Askpass скрипт создан: {askpass_file}")
            
            # Запускаем SSH
            self.process = subprocess.Popen(
                ssh_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                stdin=subprocess.DEVNULL
            )
            
            # Сохраняем путь к скрипту для последующей очистки
            self.askpass_file = askpass_file
            
            # Ждем немного для установки соединения
            time.sleep(3)
            
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
            # Очищаем временный файл при ошибке
            try:
                os.unlink(askpass_file)
            except:
                pass
            print(f"❌ Ошибка в fallback методе: {e}")
            return False
    
    def close_tunnel(self):
        """Закрывает SSH туннель"""
        if self.process:
            print("🔒 Закрытие SSH туннеля...")
            
            # Проверяем, это pexpect процесс или обычный subprocess
            if hasattr(self.process, 'terminate') and hasattr(self.process, 'isalive'):
                # pexpect процесс
                try:
                    if self.process.isalive():
                        self.process.terminate()
                        self.process.wait()
                    print("✅ SSH туннель (pexpect) закрыт")
                except Exception as e:
                    print(f"⚠️ Ошибка при закрытии pexpect туннеля: {e}")
                    try:
                        self.process.kill()
                        print("✅ SSH туннель (pexpect) принудительно закрыт")
                    except:
                        pass
            else:
                # Обычный subprocess
                try:
                    self.process.terminate()
                    self.process.wait(timeout=5)
                    print("✅ SSH туннель закрыт")
                except subprocess.TimeoutExpired:
                    print("⚠️ Принудительное завершение SSH туннеля...")
                    self.process.kill()
                    self.process.wait()
                    print("✅ SSH туннель принудительно закрыт")
                except Exception as e:
                    print(f"⚠️ Ошибка при закрытии туннеля: {e}")
            
            self.process = None
        
        # Очистка pexpect процесса
        if hasattr(self, 'pexpect_process') and self.pexpect_process:
            try:
                if self.pexpect_process.isalive():
                    self.pexpect_process.terminate()
                    self.pexpect_process.wait()
            except:
                pass
            finally:
                self.pexpect_process = None
        
        # Очищаем временный askpass файл
        if hasattr(self, 'askpass_file') and self.askpass_file:
            try:
                os.unlink(self.askpass_file)
                print("🧹 Временный askpass файл удален")
            except Exception as e:
                print(f"⚠️ Не удалось удалить askpass файл: {e}")
            finally:
                self.askpass_file = None
    
    def is_tunnel_active(self):
        """Проверяет активность SSH туннеля"""
        if not self.process:
            return False
        
        # Проверяем для pexpect процесса
        if hasattr(self.process, 'isalive'):
            return self.process.isalive()
        
        # Проверяем для обычного subprocess
        return self.process.poll() is None
    
    def get_tunnel_info(self):
        """Возвращает информацию о туннеле"""
        return {
            "local_port": self.local_port,
            "remote_host": self.remote_host,
            "remote_user": self.remote_user,
            "remote_port": self.remote_port,
            "ssh_key": str(self.key_path),
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