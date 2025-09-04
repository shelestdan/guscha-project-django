#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guscha_django.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'security%';")
tables = [row[0] for row in cursor.fetchall()]

print("Security tables found:")
for table in tables:
    print(f"  - {table}")

print("\nAll tables:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
all_tables = [row[0] for row in cursor.fetchall()]
for table in all_tables:
    print(f"  - {table}")