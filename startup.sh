#!/bin/bash

python manage.py migrate --settings=adopt_a_tree.settings_azure

python manage.py collectstatic --noinput --settings=adopt_a_tree.settings_azure

gunicorn --bind=0.0.0.0:8000 --timeout 600   adopt_a_tree.wsgi