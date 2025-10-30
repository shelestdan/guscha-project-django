#!/usr/bin/env python3
"""
Скрипт для анализа неиспользуемых Python пакетов
Сканирует код и определяет какие пакеты реально используются
"""

import os
import re
import subprocess
from pathlib import Path
from collections import defaultdict

# Цвета для вывода
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'

def get_installed_packages():
    """Получить список установленных пакетов"""
    try:
        result = subprocess.run(['pip', 'list', '--format=freeze'], 
                              capture_output=True, text=True, check=True)
        packages = {}
        for line in result.stdout.strip().split('\n'):
            if '==' in line:
                name, version = line.split('==')
                packages[name.lower()] = version
        return packages
    except Exception as e:
        print(f"{Colors.RED}Ошибка получения списка пакетов: {e}{Colors.RESET}")
        return {}

def scan_imports(directory):
    """Сканировать все Python файлы и найти импорты"""
    imports = set()
    
    for py_file in Path(directory).rglob('*.py'):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Найти все import statements
                import_pattern = r'^(?:from|import)\s+([a-zA-Z0-9_]+)'
                matches = re.finditer(import_pattern, content, re.MULTILINE)
                
                for match in matches:
                    module = match.group(1)
                    imports.add(module.lower())
        except Exception as e:
            continue
    
    return imports

def normalize_package_name(name):
    """Нормализовать имя пакета (django-cors-headers -> corsheaders)"""
    # Маппинг известных пакетов
    mappings = {
        'django-cors-headers': 'corsheaders',
        'django-filter': 'django_filters',
        'djangorestframework': 'rest_framework',
        'python-telegram-bot': 'telegram',
        'django-allauth': 'allauth',
        'django-redis': 'django_redis',
        'django-axes': 'axes',
        'django-guardian': 'guardian',
        'django-defender': 'defender',
        'django-ratelimit': 'ratelimit',
        'django-recaptcha': 'captcha',
        'django-csp': 'csp',
        'django-honeypot': 'honeypot',
        'django-unfold': 'unfold',
        'django-simple-history': 'simple_history',
        'django-crispy-forms': 'crispy_forms',
        'crispy-tailwind': 'crispy_tailwind',
        'django-import-export': 'import_export',
        'django-money': 'djmoney',
        'django-dbbackup': 'dbbackup',
        'django-otp': 'django_otp',
        'django-celery-beat': 'django_celery_beat',
        'django-celery-results': 'django_celery_results',
        'djangorestframework-simplejwt': 'rest_framework_simplejwt',
        'python-slugify': 'slugify',
        'python-dotenv': 'dotenv',
        'psycopg2-binary': 'psycopg2',
    }
    
    return mappings.get(name.lower(), name.lower().replace('-', '_'))

def main():
    print(f"\n{Colors.CYAN}=== АНАЛИЗ НЕИСПОЛЬЗУЕМЫХ ПАКЕТОВ ==={Colors.RESET}\n")
    
    # Получить установленные пакеты
    print(f"{Colors.YELLOW}Получение списка установленных пакетов...{Colors.RESET}")
    installed = get_installed_packages()
    print(f"Найдено установленных пакетов: {Colors.GREEN}{len(installed)}{Colors.RESET}\n")
    
    # Сканировать импорты
    print(f"{Colors.YELLOW}Сканирование импортов в коде...{Colors.RESET}")
    django_dir = Path('guscha_django')
    if not django_dir.exists():
        print(f"{Colors.RED}Директория guscha_django не найдена!{Colors.RESET}")
        return
    
    imports = scan_imports(django_dir)
    print(f"Найдено уникальных импортов: {Colors.GREEN}{len(imports)}{Colors.RESET}\n")
    
    # Определить используемые пакеты
    used_packages = set()
    for pkg_name in installed.keys():
        normalized = normalize_package_name(pkg_name)
        if normalized in imports or pkg_name in imports:
            used_packages.add(pkg_name)
    
    # Определить неиспользуемые пакеты
    unused = set(installed.keys()) - used_packages
    
    # Исключить системные и транзитивные зависимости
    system_packages = {
        'pip', 'setuptools', 'wheel', 'pip-tools',
        'certifi', 'charset-normalizer', 'idna', 'urllib3',
        'asgiref', 'sqlparse', 'tzdata', 'pytz',
        'six', 'python-dateutil', 'jmespath',
        'cffi', 'pycparser', 'cryptography',
        'markupsafe', 'itsdangerous', 'blinker',
        'click', 'colorama', 'vine', 'amqp', 'kombu', 'billiard',
        'httpcore', 'httpx', 'h11', 'anyio', 'sniffio',
        'botocore', 's3transfer',
    }
    
    # Подозрительные пакеты (альтернативные админки, Flask и т.д.)
    suspicious = {
        'django-admin-datta', 'django-adminlte3', 'django-jazzmin', 'django-volt-admin',
        'flask', 'flask-jwt-extended', 'flask-bcrypt',
        'django-eventstream', 'django-grip',
    }
    
    unused_filtered = unused - system_packages
    suspicious_found = unused_filtered & suspicious
    
    # Вывод результатов
    print(f"{Colors.CYAN}=== РЕЗУЛЬТАТЫ ==={Colors.RESET}\n")
    
    print(f"Всего установлено: {Colors.YELLOW}{len(installed)}{Colors.RESET}")
    print(f"Используется в коде: {Colors.GREEN}{len(used_packages)}{Colors.RESET}")
    print(f"Не используется: {Colors.RED}{len(unused_filtered)}{Colors.RESET}")
    print(f"Подозрительные: {Colors.RED}{len(suspicious_found)}{Colors.RESET}\n")
    
    if suspicious_found:
        print(f"{Colors.RED}=== ПОДОЗРИТЕЛЬНЫЕ ПАКЕТЫ (рекомендуется удалить) ==={Colors.RESET}\n")
        for pkg in sorted(suspicious_found):
            version = installed[pkg]
            print(f"  ❌ {pkg}=={version}")
        print()
        
        print(f"{Colors.YELLOW}Команда для удаления:{Colors.RESET}")
        print(f"  pip uninstall -y {' '.join(sorted(suspicious_found))}")
        print()
    
    # Другие неиспользуемые (возможно транзитивные зависимости)
    other_unused = unused_filtered - suspicious
    if other_unused and len(other_unused) < 50:
        print(f"{Colors.YELLOW}=== ДРУГИЕ НЕИСПОЛЬЗУЕМЫЕ (возможно зависимости) ==={Colors.RESET}\n")
        for pkg in sorted(other_unused):
            version = installed[pkg]
            print(f"  ⚠️  {pkg}=={version}")
        print()
    
    print(f"{Colors.GREEN}Анализ завершён!{Colors.RESET}\n")

if __name__ == '__main__':
    main()
