from django.shortcuts import render

# Простая система резервного копирования
# Управление осуществляется через админку Django и команды manage.py
# Доступные команды:
# - python manage.py dbbackup (создание резервной копии БД)
# - python manage.py mediabackup (создание резервной копии медиа-файлов)
# - python manage.py listbackups (список резервных копий)
# - python manage.py dbrestore (восстановление БД)
# - python manage.py mediarestore (восстановление медиа-файлов)