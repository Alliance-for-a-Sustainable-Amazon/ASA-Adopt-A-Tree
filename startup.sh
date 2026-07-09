#!/bin/bash

echo "Collecting static files..."
python manage.py collectstatic --noinput --settings=adopt_a_tree.settings_azure

echo "Starting gunicorn server"
gunicorn --bind=0.0.0.0:8000 --workers 1 --timeout 120 adopt_a_tree.wsgi:application