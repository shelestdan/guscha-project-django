#!/usr/bin/env python3
"""
Скрипт для автоматизации проверок безопасности Django проекта
Использует pip-audit для поиска уязвимостей в зависимостях
"""

import subprocess
import sys
import json
import os
from datetime import datetime
from pathlib import Path


def run_pip_audit():
    """
    Запускает pip-audit для проверки уязвимостей
    """
    print("🔍 Запуск проверки безопасности зависимостей...")
    
    try:
        # Запуск pip-audit с выводом в JSON формате
        result = subprocess.run(
            [sys.executable, "-m", "pip_audit", "--format=json", "--requirement", "requirements.txt"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print("✅ Уязвимости не найдены!")
            return True, None
        else:
            # Парсим JSON вывод с уязвимостями
            try:
                vulnerabilities = json.loads(result.stdout)
                return False, vulnerabilities
            except json.JSONDecodeError:
                print(f"❌ Ошибка парсинга вывода pip-audit: {result.stderr}")
                return False, None
                
    except FileNotFoundError:
        print("❌ pip-audit не установлен. Установите его командой: pip install pip-audit")
        return False, None
    except Exception as e:
        print(f"❌ Ошибка при выполнении pip-audit: {e}")
        return False, None


def save_audit_report(vulnerabilities):
    """
    Сохраняет отчет об уязвимостях в файл
    """
    if not vulnerabilities:
        return
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"security_audit_report_{timestamp}.json"
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(vulnerabilities, f, indent=2, ensure_ascii=False)
        print(f"📄 Отчет сохранен в файл: {report_file}")
    except Exception as e:
        print(f"❌ Ошибка сохранения отчета: {e}")


def print_vulnerabilities_summary(vulnerabilities):
    """
    Выводит краткую сводку найденных уязвимостей
    """
    if not vulnerabilities:
        return
        
    print("\n🚨 НАЙДЕНЫ УЯЗВИМОСТИ:")
    print("=" * 50)
    
    for vuln in vulnerabilities:
        package = vuln.get('package', 'Unknown')
        version = vuln.get('installed_version', 'Unknown')
        vuln_id = vuln.get('id', 'Unknown')
        severity = vuln.get('fix_versions', [])
        
        print(f"📦 Пакет: {package} (версия: {version})")
        print(f"🆔 ID уязвимости: {vuln_id}")
        if severity:
            print(f"🔧 Рекомендуемые версии: {', '.join(severity)}")
        print("-" * 30)


def main():
    """
    Основная функция скрипта
    """
    print("🛡️  АУДИТ БЕЗОПАСНОСТИ DJANGO ПРОЕКТА")
    print("=" * 40)
    
    # Проверяем наличие requirements.txt
    if not os.path.exists('requirements.txt'):
        print("❌ Файл requirements.txt не найден!")
        sys.exit(1)
    
    # Запускаем проверку
    is_safe, vulnerabilities = run_pip_audit()
    
    if is_safe:
        print("\n🎉 Все зависимости безопасны!")
        sys.exit(0)
    else:
        if vulnerabilities:
            print_vulnerabilities_summary(vulnerabilities)
            save_audit_report(vulnerabilities)
            
        print("\n⚠️  Рекомендуется обновить уязвимые пакеты!")
        print("💡 Используйте: pip install --upgrade <package_name>")
        sys.exit(1)


if __name__ == "__main__":
    main()