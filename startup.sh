#!/bin/bash

echo "Collect static files"
python manage.py collectstatic --noinput --settings=adopt_a_tree.settings_azure

echo "Applying migrations"
python manage.py migrate --noinput --settings=adopt_a_tree.settings_azure

echo "Creating/updating admin user"
python manage.py create_admin --settings=adopt_a_tree.settings_azure

echo "Starting gunicorn server"
gunicorn --bind=0.0.0.0:8000 --workers 1 --timeout 120 adopt_a_tree.wsgi:application