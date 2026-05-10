#!/bin/bash

# Stops script if a step fails.
set -e

echo "Applying migrations"
python manage.py migrate --settings=adopt_a_tree.settings_azure

echo " Collecting static files"
python manage.py collectstatic --noinput --settings=adopt_a_tree.settings_azure

# Creates superuser based on environment variables. If user already exists, 
# then we update the superuser login instead.
if [ -n "$DJANGO_ADMIN_USERNAME" ] && [ -n "$DJANGO_ADMIN_PASSWORD" ]; then
    echo "Creating or updating admin user"
    python << 'END'
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "adopt_a_tree.settings_azure")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = os.environ.get("DJANGO_ADMIN_USERNAME")
password = os.environ.get("DJANGO_ADMIN_PASSWORD")
email = os.environ.get("DJANGO_ADMIN_EMAIL", "admin@example.com")

user, created = User.objects.get_or_create(username=username)

user.email = email
user.set_password(password)
user.is_superuser = True
user.is_staff = True
user.save()

if created:
    print(f"Created new admin user: {username}")
else:
    print(f"Updated existing admin user: {username}")
END
fi

echo "Starting gunicorn server"
gunicorn --bind=0.0.0.0:8000 --timeout 600 adopt_a_tree.wsgi:application