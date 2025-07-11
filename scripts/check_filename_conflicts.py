#!/usr/bin/env python3
"""
Filename Conflicts Detection Script

Automatically detects potential filename conflicts with Python standard library
and common third-party modules to prevent import issues.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Set, Tuple

# Critical Python standard library modules that MUST NOT be used as filenames
FORBIDDEN_FILENAMES = {
    # Core Python modules
    'os', 'sys', 'time', 'json', 'logging', 'typing', 'pathlib', 'collections',
    'functools', 'itertools', 'operator', 're', 'math', 'datetime', 'random',
    'string', 'io', 'csv', 'sqlite3', 'urllib', 'http', 'email', 'html', 'xml',
    'multiprocessing', 'threading', 'asyncio', 'subprocess', 'shutil', 'tempfile',
    'glob', 'pickle', 'copy', 'heapq', 'bisect', 'array', 'struct', 'binascii',
    'base64', 'hashlib', 'hmac', 'secrets', 'uuid', 'decimal', 'fractions',
    'statistics', 'socket', 'ssl', 'select', 'signal', 'mmap', 'ctypes',
    'platform', 'getpass', 'traceback', 'warnings', 'contextlib', 'abc',
    'atexit', 'weakref', 'gc', 'inspect', 'types', 'enum', 'dataclasses',
    'keyword', 'token', 'tokenize', 'ast',
    
    # Testing & debugging
    'unittest', 'doctest', 'pdb', 'profile', 'pstats', 'timeit', 'cProfile',
    'trace', 'test',
    
    # File & compression
    'zipfile', 'tarfile', 'gzip', 'bz2', 'lzma', 'zlib',
    
    # Configuration & args
    'configparser', 'argparse', 'optparse', 'getopt',
    
    # Text processing
    'formatter', 'textwrap', 'unicodedata', 'stringprep', 'readline',
    'rlcompleter',
    
    # Concurrency
    'queue', 'sched', 'calendar', 'locale', 'gettext', 'codecs', 'encodings',
    
    # Import system
    'imp', 'zipimport', 'pkgutil', 'modulefinder', 'runpy', 'importlib',
    'parser', 'symbol', 'compileall'
}

# Potentially dangerous names (warn but don't fail)
POTENTIALLY_DANGEROUS = {
    'config', 'constants', 'exceptions', 'utils', 'base', 'helpers', 'models',
    'views', 'forms', 'admin', 'urls', 'settings', 'wsgi', 'asgi', 'celery',
    'tasks', 'signals', 'middleware', 'decorators', 'mixins', 'managers',
    'querysets', 'serializers', 'permissions', 'filters', 'pagination'
}

# Common third-party modules
COMMON_THIRD_PARTY = {
    'django', 'flask', 'fastapi', 'requests', 'numpy', 'pandas', 'matplotlib',
    'seaborn', 'sklearn', 'torch', 'tensorflow', 'keras', 'pillow', 'opencv',
    'boto3', 'psycopg2', 'sqlalchemy', 'redis', 'celery', 'pytest', 'click',
    'pydantic', 'marshmallow', 'alembic', 'jinja2', 'wtforms', 'gunicorn',
    'uvicorn', 'starlette', 'httpx', 'aiohttp', 'asyncpg', 'pymongo'
}

def find_python_files(directory: str) -> List[Path]:
    """Find all Python files in the directory recursively."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip common directories
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.pytest_cache', 
                                               'node_modules', '.env', 'venv', 'env',
                                               '.tox', '.coverage', 'htmlcov', '.venv'}]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    return python_files

def extract_module_name(file_path: Path) -> str:
    """Extract module name from file path."""
    return file_path.stem

def check_conflicts(python_files: List[Path]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Check for filename conflicts.
    
    Returns:
        Tuple of (critical_conflicts, warnings, third_party_conflicts)
    """
    critical_conflicts = []
    warnings = []
    third_party_conflicts = []
    
    for file_path in python_files:
        module_name = extract_module_name(file_path)
        try:
            relative_path = str(file_path.relative_to(Path.cwd()))
        except ValueError:
            # Handle case where file_path is not relative to cwd
            relative_path = str(file_path)
        
        # Check critical conflicts
        if module_name in FORBIDDEN_FILENAMES:
            critical_conflicts.append({
                'file': relative_path,
                'module_name': module_name,
                'conflict_type': 'Python Standard Library',
                'severity': 'CRITICAL'
            })
        
        # Check potentially dangerous names
        elif module_name in POTENTIALLY_DANGEROUS:
            warnings.append({
                'file': relative_path,
                'module_name': module_name,
                'conflict_type': 'Potentially Dangerous',
                'severity': 'WARNING'
            })
        
        # Check third-party conflicts
        elif module_name in COMMON_THIRD_PARTY:
            third_party_conflicts.append({
                'file': relative_path,
                'module_name': module_name,
                'conflict_type': 'Third-party Module',
                'severity': 'WARNING'
            })
    
    return critical_conflicts, warnings, third_party_conflicts

def generate_safe_alternatives(module_name: str) -> List[str]:
    """Generate safe alternative filenames."""
    alternatives = []
    
    # Common prefixes for different categories
    prefixes = [
        'app_', 'project_', 'custom_', 'service_', 'manager_', 'handler_',
        'processor_', 'controller_', 'utility_', 'helper_', 'adapter_',
        'provider_', 'factory_', 'builder_', 'parser_', 'validator_'
    ]
    
    # Common suffixes
    suffixes = [
        '_service', '_manager', '_handler', '_processor', '_controller',
        '_utility', '_helper', '_adapter', '_provider', '_factory',
        '_builder', '_parser', '_validator', '_config', '_settings'
    ]
    
    # Generate alternatives
    for prefix in prefixes[:3]:  # Top 3 prefixes
        alternatives.append(f"{prefix}{module_name}")
    
    for suffix in suffixes[:3]:  # Top 3 suffixes
        alternatives.append(f"{module_name}{suffix}")
    
    return alternatives

def print_report(critical_conflicts: List[Dict], warnings: List[Dict], 
                third_party_conflicts: List[Dict], args):
    """Print the conflict report."""
    
    print("🔍 FILENAME CONFLICTS DETECTION REPORT")
    print("=" * 50)
    
    total_files = len(critical_conflicts) + len(warnings) + len(third_party_conflicts)
    
    # Critical conflicts
    if critical_conflicts:
        print(f"\n🚨 CRITICAL CONFLICTS ({len(critical_conflicts)}):")
        print("-" * 30)
        for conflict in critical_conflicts:
            print(f"❌ {conflict['file']}")
            print(f"   Module: {conflict['module_name']}")
            print(f"   Conflicts with: {conflict['conflict_type']}")
            
            if args.suggest_alternatives:
                alternatives = generate_safe_alternatives(conflict['module_name'])
                print(f"   💡 Suggested alternatives: {', '.join(alternatives[:3])}")
            print()
    
    # Warnings
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        print("-" * 20)
        for warning in warnings:
            print(f"⚠️  {warning['file']}")
            print(f"   Module: {warning['module_name']}")
            print(f"   Type: {warning['conflict_type']}")
            
            if args.suggest_alternatives:
                alternatives = generate_safe_alternatives(warning['module_name'])
                print(f"   💡 Suggested alternatives: {', '.join(alternatives[:2])}")
            print()
    
    # Third-party conflicts
    if third_party_conflicts and args.verbose:
        print(f"\n📦 THIRD-PARTY CONFLICTS ({len(third_party_conflicts)}):")
        print("-" * 30)
        for conflict in third_party_conflicts:
            print(f"📦 {conflict['file']}")
            print(f"   Module: {conflict['module_name']}")
            print(f"   Conflicts with: {conflict['conflict_type']}")
            print()
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print(f"   Critical conflicts: {len(critical_conflicts)}")
    print(f"   Warnings: {len(warnings)}")
    print(f"   Third-party conflicts: {len(third_party_conflicts)}")
    print(f"   Total issues: {total_files}")
    
    if critical_conflicts == 0:
        print("\n✅ No critical filename conflicts found!")
    else:
        print(f"\n❌ {len(critical_conflicts)} critical conflicts must be resolved!")

def save_report(critical_conflicts: List[Dict], warnings: List[Dict], 
               third_party_conflicts: List[Dict], output_file: str):
    """Save report to JSON file."""
    report = {
        'scan_date': str(Path.cwd()),
        'critical_conflicts': critical_conflicts,
        'warnings': warnings,
        'third_party_conflicts': third_party_conflicts,
        'summary': {
            'critical_count': len(critical_conflicts),
            'warning_count': len(warnings),
            'third_party_count': len(third_party_conflicts),
            'total_issues': len(critical_conflicts) + len(warnings) + len(third_party_conflicts)
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Report saved to: {output_file}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Check for filename conflicts with Python modules"
    )
    parser.add_argument(
        '--strict', 
        action='store_true',
        help='Exit with error code if critical conflicts found'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output including third-party conflicts'
    )
    parser.add_argument(
        '--suggest-alternatives',
        action='store_true',
        help='Suggest alternative filenames for conflicts'
    )
    parser.add_argument(
        '--output', '-o',
        help='Save report to JSON file'
    )
    parser.add_argument(
        '--directory', '-d',
        default='.',
        help='Directory to scan (default: current directory)'
    )
    
    args = parser.parse_args()
    
    # Find Python files
    python_files = find_python_files(args.directory)
    
    if not python_files:
        print("No Python files found in the directory.")
        return 0
    
    # Check conflicts
    critical_conflicts, warnings, third_party_conflicts = check_conflicts(python_files)
    
    # Print report
    print_report(critical_conflicts, warnings, third_party_conflicts, args)
    
    # Save report if requested
    if args.output:
        save_report(critical_conflicts, warnings, third_party_conflicts, args.output)
    
    # Exit with appropriate code
    if args.strict and critical_conflicts:
        print(f"\n🚨 STRICT MODE: Exiting with error code due to {len(critical_conflicts)} critical conflicts!")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 