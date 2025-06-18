#!/usr/bin/env python3
"""
🔧 Автоматическая миграция нативного логгирования на единую систему

Этот скрипт автоматически мигрирует все файлы проекта с нативного 
logging.getLogger(__name__) на unified logging систему.

ЭТАП 1 ПЛАНА: Массовая миграция нативного логгирования
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import argparse


class LoggingMigrator:
    """Автоматический мигратор системы логгирования."""
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.stats = {
            'files_processed': 0,
            'files_modified': 0,
            'import_replacements': 0,
            'logger_replacements': 0,
            'errors': 0
        }
        
        # Файлы для исключения из миграции
        self.exclude_files = {
            'core/monitoring/logger.py',  # Это источник get_logger
            'core/config/logging.py',     # Конфигурация логгирования  
            'scripts/migrate_logging.py', # Этот скрипт
            'tests/',                    # Тесты могут остаться с нативным
            'docs/',                     # Документация
            'PLAN_DOCS/',               # Планы
            '.venv/',                   # Виртуальное окружение
            '__pycache__/'              # Кеш Python
        }
        
        # Паттерны для замены
        self.patterns = [
            # Импорт logging
            (
                r'^import logging$',
                'from core.monitoring.logger import get_logger'
            ),
            # logger = logging.getLogger(__name__)
            (
                r'logger = logging\.getLogger\(__name__\)',
                'logger = get_logger(__name__)'
            ),
            # Другие варианты создания логгера
            (
                r'logging\.getLogger\(__name__\)',
                'get_logger(__name__)'
            ),
            # self.logger = logging.getLogger(...)
            (
                r'self\.logger = logging\.getLogger\(([^)]+)\)',
                r'self.logger = get_logger(\1)'
            )
        ]
    
    def should_exclude_file(self, file_path: str) -> bool:
        """Проверить, нужно ли исключить файл из миграции."""
        file_path_normalized = file_path.replace('\\', '/')
        
        for exclude_pattern in self.exclude_files:
            if exclude_pattern in file_path_normalized:
                return True
        
        return False
    
    def find_python_files(self, root_dir: str) -> List[str]:
        """Найти все Python файлы для миграции."""
        python_files = []
        
        for root, dirs, files in os.walk(root_dir):
            # Исключаем .git, .venv и другие системные папки
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, root_dir)
                    
                    if not self.should_exclude_file(relative_path):
                        python_files.append(file_path)
        
        return python_files
    
    def analyze_file(self, file_path: str) -> Dict:
        """Анализировать файл на предмет необходимости миграции."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                'needs_migration': False,
                'has_import_logging': 'import logging' in content,
                'has_getlogger': 'logging.getLogger' in content,
                'async_functions': len(re.findall(r'async def', content)),
                'total_lines': len(content.splitlines())
            }
            
            analysis['needs_migration'] = analysis['has_import_logging'] or analysis['has_getlogger']
            
            return analysis
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Ошибка анализа {file_path}: {e}")
            self.stats['errors'] += 1
            return {'needs_migration': False, 'error': str(e)}
    
    def migrate_file(self, file_path: str) -> bool:
        """Мигрировать отдельный файл."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            modified_content = original_content
            changes_made = 0
            
            # Применяем все паттерны замены
            for pattern, replacement in self.patterns:
                new_content, replacements = re.subn(pattern, replacement, modified_content, flags=re.MULTILINE)
                if replacements > 0:
                    modified_content = new_content
                    changes_made += replacements
                    
                    if 'import logging' in pattern:
                        self.stats['import_replacements'] += replacements
                    elif 'getLogger' in pattern:
                        self.stats['logger_replacements'] += replacements
            
            # Если есть изменения, записываем файл
            if changes_made > 0:
                if not self.dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(modified_content)
                
                if self.verbose:
                    print(f"✅ Мигрирован: {file_path} ({changes_made} изменений)")
                
                self.stats['files_modified'] += 1
                return True
            
            return False
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Ошибка миграции {file_path}: {e}")
            self.stats['errors'] += 1
            return False
    
    def run_migration(self, root_dir: str = '.') -> Dict:
        """Запустить полную миграцию."""
        print("🔧 Начинаю массовую миграцию логгирования...")
        print(f"{'🔍 DRY RUN режим' if self.dry_run else '🚀 Реальная миграция'}")
        print()
        
        # Найти все Python файлы
        python_files = self.find_python_files(root_dir)
        print(f"📊 Найдено {len(python_files)} Python файлов для анализа")
        
        # Анализ и миграция
        files_needing_migration = []
        
        for file_path in python_files:
            self.stats['files_processed'] += 1
            
            analysis = self.analyze_file(file_path)
            if analysis.get('needs_migration', False):
                files_needing_migration.append((file_path, analysis))
        
        print(f"🎯 Файлов требующих миграции: {len(files_needing_migration)}")
        print()
        
        # Выполнить миграцию
        if files_needing_migration:
            print("🔄 Выполняю миграцию...")
            
            for file_path, analysis in files_needing_migration:
                migrated = self.migrate_file(file_path)
                
                if migrated and self.verbose:
                    print(f"  📝 {os.path.relpath(file_path)}")
        
        return self.stats
    
    def print_summary(self):
        """Вывести итоговую статистику."""
        print("\n" + "="*60)
        print("📊 ИТОГИ МИГРАЦИИ ЛОГГИРОВАНИЯ")
        print("="*60)
        print(f"Файлов обработано: {self.stats['files_processed']}")
        print(f"Файлов изменено: {self.stats['files_modified']}")
        print(f"Import заменено: {self.stats['import_replacements']}")
        print(f"Logger заменено: {self.stats['logger_replacements']}")
        print(f"Ошибок: {self.stats['errors']}")
        print()
        
        if self.stats['files_modified'] > 0:
            if self.dry_run:
                print("🔍 DRY RUN завершён. Запустите без --dry-run для реальной миграции.")
            else:
                print("✅ Миграция завершена успешно!")
                print()
                print("🎯 СЛЕДУЮЩИЕ ШАГИ:")
                print("1. Проверьте импорты: python -c \"from main import *\"")
                print("2. Запустите тесты: python -m pytest tests/unit/test_middleware.py")
                print("3. Проверьте работу API: python main.py")
        else:
            print("ℹ️ Файлов для миграции не найдено.")


def main():
    """Основная функция скрипта."""
    parser = argparse.ArgumentParser(
        description="Автоматическая миграция логгирования на единую систему"
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true', 
        help="Режим тестового запуска без изменения файлов"
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help="Подробный вывод процесса миграции"
    )
    parser.add_argument(
        '--root-dir',
        default='.',
        help="Корневая директория для миграции (по умолчанию: текущая)"
    )
    
    args = parser.parse_args()
    
    migrator = LoggingMigrator(dry_run=args.dry_run, verbose=args.verbose)
    
    try:
        stats = migrator.run_migration(args.root_dir)
        migrator.print_summary()
        
        # Возвращаем код ошибки если были проблемы
        if stats['errors'] > 0:
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Миграция прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 