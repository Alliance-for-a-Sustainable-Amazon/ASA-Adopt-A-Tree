#!/bin/bash
set -e

echo "Migrating database"
python manage.py migrate --noinput --settings=adopt_a_tree.settings_azure

echo "Collecting static files"
python manage.py collectstatic --noinput --settings=adopt_a_tree.settings_azure

echo "Creating/updating admin"
python manage.py create_admin --settings=adopt_a_tree.settings_azure

echo "Deployment complete"