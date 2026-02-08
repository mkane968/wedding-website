#!/usr/bin/env python
"""Create a superuser non-interactively."""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wedding_site.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Create superuser
username = 'admin'
email = 'admin@example.com'
password = 'admin123'  # Change this to a secure password

if User.objects.filter(username=username).exists():
    print(f'Superuser "{username}" already exists.')
else:
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'Superuser "{username}" created successfully!')
    print(f'Username: {username}')
    print(f'Password: {password}')
    print('\n⚠️  Please change the password after first login!')
