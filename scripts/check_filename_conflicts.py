#!/usr/bin/env python3
"""
🚨 АВТОМАТИЧЕСКАЯ ПРОВЕРКА КОНФЛИКТОВ ИМЕН ФАЙЛОВ

Скрипт для обнаружения и предотвращения конфликтов имен файлов 
со стандартными модулями Python.

Usage:
    python scripts/check_filename_conflicts.py [--strict] [--fix] [--report]
"""

import os
import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
import importlib.util
import traceback

# 🔥 КРИТИЧЕСКИ ЗАПРЕЩЕННЫЕ ИМЕНА ФАЙЛОВ
CRITICAL_CONFLICTS = {
    # === CORE PYTHON MODULES ===
    "os.py", "sys.py", "time.py", "json.py", "logging.py", "typing.py", 
    "pathlib.py", "collections.py", "functools.py", "itertools.py", 
    "operator.py", "re.py", "math.py", "datetime.py", "random.py",
    "string.py", "io.py", "csv.py", "sqlite3.py", "urllib.py", "http.py",
    "email.py", "html.py", "xml.py", "multiprocessing.py", "threading.py",
    "asyncio.py", "subprocess.py", "shutil.py", "tempfile.py", "glob.py",
    "pickle.py", "copy.py", "heapq.py", "bisect.py", "array.py", "struct.py",
    "binascii.py", "base64.py", "hashlib.py", "hmac.py", "secrets.py",
    "uuid.py", "decimal.py", "fractions.py", "statistics.py", "socket.py",
    "ssl.py", "select.py", "signal.py", "mmap.py", "ctypes.py", "platform.py",
    "getpass.py", "traceback.py", "warnings.py", "contextlib.py", "abc.py",
    "atexit.py", "weakref.py", "gc.py", "inspect.py", "types.py", "enum.py",
    "dataclasses.py", "keyword.py", "token.py", "tokenize.py", "ast.py",
    
    # === TESTING & DEBUGGING ===
    "unittest.py", "doctest.py", "pdb.py", "profile.py", "pstats.py",
    "timeit.py", "cProfile.py", "trace.py", "test.py",
    
    # === FILE & COMPRESSION ===
    "zipfile.py", "tarfile.py", "gzip.py", "bz2.py", "lzma.py", "zlib.py",
    
    # === CONFIGURATION & ARGS ===
    "configparser.py", "argparse.py", "optparse.py", "getopt.py",
    
    # === TEXT PROCESSING ===
    "formatter.py", "textwrap.py", "unicodedata.py", "stringprep.py",
    "readline.py", "rlcompleter.py",
    
    # === CONCURRENCY ===
    "queue.py", "sched.py", "calendar.py", "locale.py", "gettext.py",
    "codecs.py", "encodings.py",
    
    # === IMPORT SYSTEM ===
    "imp.py", "zipimport.py", "pkgutil.py", "modulefinder.py", "runpy.py",
    "importlib.py", "parser.py", "symbol.py", "compileall.py"
}

# ⚠️ ПОТЕНЦИАЛЬНО ОПАСНЫЕ ИМЕНА
POTENTIALLY_DANGEROUS = {
    "config.py": "app_config.py, settings.py, configuration.py",
    "constants.py": "app_constants.py, project_constants.py",
    "exceptions.py": "custom_exceptions.py, app_exceptions.py",
    "utils.py": "helpers.py, utilities.py, common.py",
    "base.py": "base_classes.py, abstract_base.py, foundation.py",
    "helpers.py": "utilities.py, common.py, tools.py",
    "models.py": "data_models.py, domain_models.py, entities.py",
    "views.py": "api_views.py, web_views.py, endpoints.py"
}

# 📁 ДИРЕКТОРИИ ДЛЯ ИСКЛЮЧЕНИЯ ИЗ ПРОВЕРКИ
EXCLUDED_DIRS = {
    ".git", "__pycache__", ".venv", "venv", ".env", "node_modules",
    ".pytest_cache", ".mypy_cache", ".tox", "build", "dist", 
    ".eggs", "*.egg-info", ".coverage", "htmlcov"
}


class ConflictChecker:
    """Класс для проверки конфликтов имен файлов."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.critical_conflicts: List[Tuple[str, str]] = []
        self.potential_conflicts: List[Tuple[str, str, str]] = []
        self.all_python_files: List[Path] = []
        
    def scan_python_files(self) -> List[Path]:
        """Сканирует все Python файлы в проекте."""
        python_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Исключаем директории из EXCLUDED_DIRS
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    python_files.append(file_path)
        
        self.all_python_files = python_files
        return python_files
    
    def check_critical_conflicts(self) -> List[Tuple[str, str]]:
        """Проверяет критические конфликты имен."""
        conflicts = []
        
        for file_path in self.all_python_files:
            filename = file_path.name
            
            if filename in CRITICAL_CONFLICTS:
                relative_path = file_path.relative_to(self.project_root)
                conflicts.append((str(relative_path), filename))
        
        self.critical_conflicts = conflicts
        return conflicts
    
    def check_potential_conflicts(self) -> List[Tuple[str, str, str]]:
        """Проверяет потенциальные конфликты имен."""
        conflicts = []
        
        for file_path in self.all_python_files:
            filename = file_path.name
            
            if filename in POTENTIALLY_DANGEROUS:
                relative_path = file_path.relative_to(self.project_root)
                alternatives = POTENTIALLY_DANGEROUS[filename]
                conflicts.append((str(relative_path), filename, alternatives))
        
        self.potential_conflicts = conflicts
        return conflicts
    
    def test_import_conflicts(self) -> List[Tuple[str, str, str]]:
        """Тестирует реальные конфликты импортов."""
        import_conflicts = []
        
        # Сохраняем текущий sys.path
        original_path = sys.path.copy()
        
        try:
            for file_path in self.all_python_files:
                filename = file_path.name
                module_name = filename[:-3]  # убираем .py
                
                # Добавляем директорию файла в sys.path
                file_dir = str(file_path.parent)
                if file_dir not in sys.path:
                    sys.path.insert(0, file_dir)
                
                try:
                    # Пытаемся импортировать стандартный модуль
                    if module_name in [f[:-3] for f in CRITICAL_CONFLICTS]:
                        try:
                            # Проверяем, можем ли мы импортировать стандартный модуль
                            spec = importlib.util.find_spec(module_name)
                            if spec and spec.origin:
                                # Если spec.origin указывает на наш файл, это конфликт
                                if str(file_path) in spec.origin:
                                    relative_path = file_path.relative_to(self.project_root)
                                    import_conflicts.append((
                                        str(relative_path),
                                        module_name,
                                        f"Conflicts with stdlib module {module_name}"
                                    ))
                        except Exception as e:
                            # Если импорт падает, это тоже может быть признаком конфликта
                            pass
                            
                except Exception:
                    pass
                
        finally:
            # Восстанавливаем sys.path
            sys.path = original_path
        
        return import_conflicts
    
    def generate_report(self) -> Dict:
        """Генерирует отчет о конфликтах."""
        return {
            "project_root": str(self.project_root),
            "total_python_files": len(self.all_python_files),
            "critical_conflicts": {
                "count": len(self.critical_conflicts),
                "files": [{"path": path, "filename": name} for path, name in self.critical_conflicts]
            },
            "potential_conflicts": {
                "count": len(self.potential_conflicts),
                "files": [
                    {"path": path, "filename": name, "alternatives": alt} 
                    for path, name, alt in self.potential_conflicts
                ]
            },
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Генерирует рекомендации по исправлению."""
        recommendations = []
        
        if self.critical_conflicts:
            recommendations.append("🚨 КРИТИЧНО: Немедленно переименуйте файлы с критическими конфликтами!")
            for path, filename in self.critical_conflicts:
                if filename == "logging.py":
                    recommendations.append(f"  {path} → log_config.py или logger_config.py")
                elif filename == "types.py":
                    recommendations.append(f"  {path} → type_definitions.py или data_types.py")
                elif filename == "config.py":
                    recommendations.append(f"  {path} → app_config.py или settings.py")
                else:
                    recommendations.append(f"  {path} → {filename.replace('.py', '_module.py')}")
        
        if self.potential_conflicts:
            recommendations.append("⚠️ ВНИМАНИЕ: Рассмотрите переименование потенциально опасных файлов:")
            for path, filename, alternatives in self.potential_conflicts:
                recommendations.append(f"  {path} → {alternatives}")
        
        if not self.critical_conflicts and not self.potential_conflicts:
            recommendations.append("✅ Отлично! Конфликтов имен файлов не обнаружено.")
        
        return recommendations
    
    def auto_fix_conflicts(self, dry_run: bool = True) -> List[str]:
        """Автоматически исправляет конфликты (опционально в режиме dry-run)."""
        fixes = []
        
        for path, filename in self.critical_conflicts:
            old_path = self.project_root / path
            
            # Генерируем новое имя
            if filename == "logging.py":
                new_filename = "log_config.py"
            elif filename == "types.py":
                new_filename = "type_definitions.py"
            elif filename == "config.py":
                new_filename = "app_config.py"
            else:
                new_filename = filename.replace('.py', '_module.py')
            
            new_path = old_path.parent / new_filename
            
            if dry_run:
                fixes.append(f"WOULD RENAME: {path} → {new_path.relative_to(self.project_root)}")
            else:
                try:
                    old_path.rename(new_path)
                    fixes.append(f"RENAMED: {path} → {new_path.relative_to(self.project_root)}")
                except Exception as e:
                    fixes.append(f"FAILED: {path} - {str(e)}")
        
        return fixes


def main():
    """Основная функция."""
    parser = argparse.ArgumentParser(
        description="Проверка конфликтов имен файлов со стандартными модулями Python"
    )
    parser.add_argument(
        "--strict", 
        action="store_true", 
        help="Строгий режим: завершить с ошибкой при обнаружении конфликтов"
    )
    parser.add_argument(
        "--fix", 
        action="store_true", 
        help="Автоматически исправить критические конфликты"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Показать что будет исправлено без реальных изменений"
    )
    parser.add_argument(
        "--report", 
        type=str, 
        help="Сохранить отчет в JSON файл"
    )
    parser.add_argument(
        "--project-root", 
        type=str, 
        default=".", 
        help="Корневая директория проекта (по умолчанию: текущая)"
    )
    
    args = parser.parse_args()
    
    # Инициализируем проверщик
    checker = ConflictChecker(args.project_root)
    
    print("🔍 Сканирование Python файлов...")
    python_files = checker.scan_python_files()
    print(f"   Найдено {len(python_files)} Python файлов")
    
    print("\n🚨 Проверка критических конфликтов...")
    critical = checker.check_critical_conflicts()
    
    print("\n⚠️ Проверка потенциальных конфликтов...")
    potential = checker.check_potential_conflicts()
    
    # Генерируем отчет
    report = checker.generate_report()
    
    # Выводим результаты
    print("\n" + "="*60)
    print("📊 ОТЧЕТ О КОНФЛИКТАХ ИМЕН ФАЙЛОВ")
    print("="*60)
    
    print(f"📁 Проект: {report['project_root']}")
    print(f"📄 Всего Python файлов: {report['total_python_files']}")
    
    if report['critical_conflicts']['count'] > 0:
        print(f"\n🚨 КРИТИЧЕСКИЕ КОНФЛИКТЫ: {report['critical_conflicts']['count']}")
        for file_info in report['critical_conflicts']['files']:
            print(f"   ❌ {file_info['path']} (конфликт с {file_info['filename'][:-3]})")
    
    if report['potential_conflicts']['count'] > 0:
        print(f"\n⚠️ ПОТЕНЦИАЛЬНЫЕ КОНФЛИКТЫ: {report['potential_conflicts']['count']}")
        for file_info in report['potential_conflicts']['files']:
            print(f"   ⚠️ {file_info['path']}")
            print(f"      Альтернативы: {file_info['alternatives']}")
    
    print("\n💡 РЕКОМЕНДАЦИИ:")
    for rec in report['recommendations']:
        print(f"   {rec}")
    
    # Автоисправление
    if args.fix or args.dry_run:
        print(f"\n🔧 {'РЕЖИМ ПРЕДПРОСМОТРА' if args.dry_run else 'АВТОИСПРАВЛЕНИЕ'}:")
        fixes = checker.auto_fix_conflicts(dry_run=args.dry_run)
        for fix in fixes:
            print(f"   {fix}")
    
    # Сохранение отчета
    if args.report:
        with open(args.report, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n📄 Отчет сохранен: {args.report}")
    
    # Строгий режим
    if args.strict and (critical or potential):
        print(f"\n❌ СТРОГИЙ РЕЖИМ: Обнаружены конфликты!")
        sys.exit(1)
    
    if not critical and not potential:
        print(f"\n✅ ОТЛИЧНО: Конфликтов имен файлов не обнаружено!")
        sys.exit(0)
    else:
        print(f"\n⚠️ Обнаружены конфликты. Рекомендуется исправление.")
        sys.exit(1 if critical else 0)


if __name__ == "__main__":
    main() 