#!/bin/bash
set -e

echo "Collecting static files"
python manage.py collectstatic --noinput --settings=adopt_a_tree.settings_azure

echo "Deployment complete"