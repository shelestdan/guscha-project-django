#!/usr/bin/env python
"""
Скрипт для сборки и развертывания React фронтенда
"""

import os
import subprocess
import shutil
from pathlib import Path

# Пути
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "guscha_django_frontend"
BUILD_DIR = FRONTEND_DIR / "build"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static_root"

def run_command(command, cwd=None):
    """Выполнение команды в терминале"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✓ {command}")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Ошибка при выполнении: {command}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

def build_frontend():
    """Сборка React приложения"""
    print("🚀 Сборка React приложения...")
    
    # Проверяем наличие package.json
    if not (FRONTEND_DIR / "package.json").exists():
        print("✗ package.json не найден")
        return False
    
    # Устанавливаем зависимости
    print("📦 Установка зависимостей...")
    if not run_command("npm install", cwd=FRONTEND_DIR):
        return False
    
    # Сборка проекта
    print("🔨 Сборка проекта...")
    if not run_command("npm run build", cwd=FRONTEND_DIR):
        return False
    
    return True

def copy_build_files():
    """Копирование собранных файлов"""
    print("📁 Копирование файлов...")
    
    # Создаем директории если их нет
    TEMPLATES_DIR.mkdir(exist_ok=True)
    
    # Копируем index.html в templates
    src_index = BUILD_DIR / "index.html"
    dst_index = TEMPLATES_DIR / "index.html"
    
    if src_index.exists():
        shutil.copy2(src_index, dst_index)
        print(f"✓ Скопирован {src_index} -> {dst_index}")
    else:
        print("✗ index.html не найден в build директории")
        return False
    
    # Копируем статические файлы
    src_static = BUILD_DIR / "static"
    dst_static = STATIC_DIR / "static"
    
    if src_static.exists():
        if dst_static.exists():
            shutil.rmtree(dst_static)
        shutil.copytree(src_static, dst_static)
        print(f"✓ Скопированы статические файлы")
    else:
        print("✗ static директория не найдена в build")
        return False
    
    return True

def collect_static():
    """Сборка статических файлов Django"""
    print("📊 Сборка статических файлов Django...")
    return run_command("python manage.py collectstatic --noinput", cwd=BASE_DIR)

def main():
    """Основная функция"""
    print("=" * 50)
    print("🚀 Развертывание React фронтенда")
    print("=" * 50)
    
    # Сборка фронтенда
    if not build_frontend():
        print("❌ Ошибка при сборке фронтенда")
        return
    
    # Копирование файлов
    if not copy_build_files():
        print("❌ Ошибка при копировании файлов")
        return
    
    # Сборка статики Django
    if not collect_static():
        print("❌ Ошибка при сборке статики Django")
        return
    
    print("=" * 50)
    print("✅ Развертывание завершено успешно!")
    print("=" * 50)
    print("Теперь вы можете запустить Django сервер: ")
    print("python manage.py runserver")

if __name__ == "__main__":
    main()