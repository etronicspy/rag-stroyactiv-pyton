#!/usr/bin/env python3
"""
PostgreSQL диагностическая утилита.

Простая утилита для проверки состояния подключения к PostgreSQL и диагностики проблем.
"""
import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.config import get_settings
from core.database.adapters.postgresql_adapter import PostgreSQLAdapter
from core.database.exceptions import ConnectionError, DatabaseError
from core.monitoring.logger import get_logger

logger = get_logger(__name__)


class PostgreSQLDiagnostic:
    """PostgreSQL диагностический класс."""
    
    def __init__(self):
        """Инициализация диагностики."""
        self.settings = get_settings()
        self.config = self.settings.get_relational_db_config()
        self.adapter = None
        
    async def __aenter__(self):
        """Асинхронный контекстный менеджер - вход."""
        try:
            self.adapter = PostgreSQLAdapter(self.config)
            return self
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL adapter: {e}")
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекстный менеджер - выход."""
        if self.adapter:
            await self.adapter.close()
    
    def print_header(self, title: str):
        """Печать заголовка диагностики."""
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}")
    
    def print_section(self, title: str):
        """Печать заголовка секции."""
        print(f"\n📋 {title}")
        print("-" * 40)
    
    def print_result(self, status: str, message: str, details: Optional[str] = None):
        """Печать результата проверки."""
        icon = "✅" if status == "success" else "❌" if status == "error" else "⚠️"
        print(f"{icon} {message}")
        if details:
            print(f"   └─ {details}")
    
    async def check_configuration(self) -> bool:
        """Проверка конфигурации PostgreSQL."""
        self.print_section("Configuration Check")
        
        try:
            # Проверяем основные настройки
            if self.settings.DISABLE_POSTGRESQL_CONNECTION:
                self.print_result("warning", "PostgreSQL connection is disabled", 
                                "Set DISABLE_POSTGRESQL_CONNECTION=false to enable")
                return False
            
            if not self.config.get("connection_string"):
                self.print_result("error", "PostgreSQL connection string is missing",
                                "Check POSTGRESQL_URL in environment")
                return False
            
            self.print_result("success", "Configuration loaded successfully")
            
            # Выводим основные параметры
            connection_string = self.config["connection_string"]
            # Маскируем пароль для безопасности
            safe_connection = connection_string.replace(
                connection_string.split("@")[0].split(":")[-1], "***"
            ) if "@" in connection_string else connection_string
            
            print(f"   └─ Connection: {safe_connection}")
            print(f"   └─ Pool size: {self.config.get('pool_size', 'default')}")
            print(f"   └─ Max overflow: {self.config.get('max_overflow', 'default')}")
            print(f"   └─ Pool timeout: {self.config.get('pool_timeout', 'default')}s")
            
            return True
            
        except Exception as e:
            self.print_result("error", "Configuration check failed", str(e))
            return False
    
    async def check_connection(self) -> bool:
        """Проверка подключения к PostgreSQL."""
        self.print_section("Connection Check")
        
        try:
            if not self.adapter:
                self.print_result("error", "PostgreSQL adapter not initialized")
                return False
            
            # Проверяем health check
            health_status = await self.adapter.health_check()
            
            if health_status.get("status") == "healthy":
                self.print_result("success", "PostgreSQL connection is healthy")
                
                # Выводим детали подключения
                response_time = health_status.get("response_time", "unknown")
                print(f"   └─ Response time: {response_time}")
                
                if "details" in health_status:
                    details = health_status["details"]
                    print(f"   └─ Server info: {details.get('server_info', 'N/A')}")
                
                return True
            else:
                self.print_result("error", "PostgreSQL connection unhealthy", 
                                health_status.get("error", "Unknown error"))
                return False
                
        except Exception as e:
            self.print_result("error", "Connection check failed", str(e))
            return False
    
    async def check_database_info(self) -> bool:
        """Проверка информации о базе данных."""
        self.print_section("Database Information")
        
        try:
            query = """
            SELECT 
                version() as version,
                current_database() as database,
                current_user as user,
                inet_server_addr() as server_ip,
                inet_server_port() as server_port,
                pg_postmaster_start_time() as server_start_time,
                pg_is_in_recovery() as is_replica
            """
            result = await self.adapter.execute_query(query)
            
            if result and len(result) > 0:
                info = result[0]
                self.print_result("success", "Database information retrieved")
                
                print(f"   └─ Version: {info.get('version', 'N/A')}")
                print(f"   └─ Database: {info.get('database', 'N/A')}")
                print(f"   └─ User: {info.get('user', 'N/A')}")
                print(f"   └─ Server IP: {info.get('server_ip', 'N/A')}")
                print(f"   └─ Server Port: {info.get('server_port', 'N/A')}")
                print(f"   └─ Server Start: {info.get('server_start_time', 'N/A')}")
                print(f"   └─ Is Replica: {info.get('is_replica', 'N/A')}")
                
                return True
            else:
                self.print_result("warning", "Database info query returned no results")
                return False
                
        except Exception as e:
            self.print_result("error", "Database info check failed", str(e))
            return False
    
    async def check_extensions(self) -> bool:
        """Проверка PostgreSQL расширений."""
        self.print_section("PostgreSQL Extensions")
        
        try:
            query = """
            SELECT extname as name, extversion as version, extrelocatable as relocatable
            FROM pg_extension 
            ORDER BY extname
            """
            result = await self.adapter.execute_query(query)
            
            if result:
                extensions = {row["name"]: row for row in result}
                self.print_result("success", f"Found {len(extensions)} extensions")
                
                # Проверяем важные расширения
                important_extensions = {
                    "pg_trgm": "Trigram similarity (needed for fuzzy search)",
                    "btree_gin": "GIN btree support (useful for indexes)", 
                    "pgvector": "Vector similarity search (optional)",
                    "uuid-ossp": "UUID generation functions"
                }
                
                for ext_name, description in important_extensions.items():
                    if ext_name in extensions:
                        ext_info = extensions[ext_name]
                        print(f"   ✅ {ext_name} v{ext_info['version']} - {description}")
                    else:
                        print(f"   ❌ {ext_name} - {description}")
                
                # Показываем все остальные расширения
                other_extensions = [name for name in extensions.keys() 
                                 if name not in important_extensions]
                if other_extensions:
                    print(f"   📋 Other extensions: {', '.join(other_extensions)}")
                
                return True
            else:
                self.print_result("warning", "No extensions found")
                return False
                
        except Exception as e:
            self.print_result("error", "Extensions check failed", str(e))
            return False
    
    async def check_tables(self) -> bool:
        """Проверка таблиц в базе данных."""
        self.print_section("Database Tables")
        
        try:
            query = """
            SELECT 
                table_name,
                table_type,
                is_insertable_into as writable
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
            """
            result = await self.adapter.execute_query(query)
            
            if result:
                tables = [row["table_name"] for row in result]
                self.print_result("success", f"Found {len(tables)} tables")
                
                # Проверяем важные таблицы
                important_tables = [
                    "alembic_version",  # Миграции
                    "materials",        # Основные материалы
                    "raw_products"      # Сырые продукты
                ]
                
                for table_name in important_tables:
                    if table_name in tables:
                        print(f"   ✅ {table_name}")
                    else:
                        print(f"   ❌ {table_name} (missing)")
                
                # Показываем все остальные таблицы  
                other_tables = [name for name in tables if name not in important_tables]
                if other_tables:
                    print(f"   📋 Other tables: {', '.join(other_tables)}")
                
                return len(tables) > 0
            else:
                self.print_result("warning", "No tables found", 
                                "Run 'alembic upgrade head' to create tables")
                return False
                
        except Exception as e:
            self.print_result("error", "Tables check failed", str(e))
            return False
    
    async def check_migrations(self) -> bool:
        """Проверка миграций Alembic."""
        self.print_section("Database Migrations")
        
        try:
            query = "SELECT version_num FROM alembic_version LIMIT 1"
            result = await self.adapter.execute_query(query)
            
            if result and len(result) > 0:
                current_version = result[0]["version_num"]
                self.print_result("success", f"Current migration version: {current_version}")
                return True
            else:
                self.print_result("warning", "No migration version found",
                                "Alembic migrations may not be initialized")
                return False
                
        except Exception as e:
            if "does not exist" in str(e).lower():
                self.print_result("warning", "alembic_version table does not exist",
                                "Run 'alembic upgrade head' to initialize migrations")
            else:
                self.print_result("error", "Migration check failed", str(e))
            return False
    
    async def check_performance(self) -> bool:
        """Проверка производительности подключений."""
        self.print_section("Performance Check")
        
        try:
            # Измеряем время простого запроса
            start_time = datetime.now()
            await self.adapter.execute_query("SELECT 1")
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            
            self.print_result("success", f"Query response time: {query_time:.2f}ms")
            
            if query_time < 10:
                print("   └─ Performance: Excellent")
            elif query_time < 50:
                print("   └─ Performance: Good")
            elif query_time < 100:
                print("   └─ Performance: Fair")
            else:
                print("   └─ Performance: Slow (check network/server)")
            
            # Проверяем настройки connection pool
            pool_info = {
                "pool_size": self.config.get("pool_size", 10),
                "max_overflow": self.config.get("max_overflow", 20),
                "pool_timeout": self.config.get("pool_timeout", 30)
            }
            
            print(f"   └─ Pool settings: {pool_info}")
            
            return True
            
        except Exception as e:
            self.print_result("error", "Performance check failed", str(e))
            return False
    
    async def run_full_diagnostic(self) -> Dict[str, bool]:
        """Запуск полной диагностики PostgreSQL."""
        self.print_header("PostgreSQL Full Diagnostic")
        
        results = {}
        
        # Последовательно запускаем все проверки
        checks = [
            ("Configuration", self.check_configuration),
            ("Connection", self.check_connection),
            ("Database Info", self.check_database_info),
            ("Extensions", self.check_extensions),
            ("Tables", self.check_tables),
            ("Migrations", self.check_migrations),
            ("Performance", self.check_performance)
        ]
        
        for check_name, check_func in checks:
            try:
                results[check_name] = await check_func()
            except Exception as e:
                logger.error(f"{check_name} check failed: {e}")
                results[check_name] = False
        
        # Выводим итоговый отчет
        self.print_section("Diagnostic Summary")
        
        successful = sum(1 for result in results.values() if result)
        total = len(results)
        
        print(f"📊 Overall Results: {successful}/{total} checks passed")
        
        for check_name, result in results.items():
            status = "✅" if result else "❌"
            print(f"   {status} {check_name}")
        
        if successful == total:
            print("\n🎉 PostgreSQL is fully operational!")
        elif successful >= total * 0.7:
            print("\n⚠️ PostgreSQL is mostly operational with some issues")
        else:
            print("\n❌ PostgreSQL has significant issues that need attention")
        
        return results


async def main():
    """Основная функция для запуска диагностики."""
    try:
        async with PostgreSQLDiagnostic() as diagnostic:
            await diagnostic.run_full_diagnostic()
            
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        logger.error(f"PostgreSQL diagnostic failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 