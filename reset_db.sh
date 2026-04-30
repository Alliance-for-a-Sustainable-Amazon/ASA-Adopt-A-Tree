#!bin/bash

echo "DATABASE RESET SCRIPT"
echo "This will delete ALL data but keep the schema."

# Environment protection. Prevents the reset script from being run in production.
if [ "$DJANGO_ENV" = "production" ]; then
    echo "ERROR: Cannot run reset script in production."
    exit 1
fi

# Confirms that user wants to run reset script.
read -p "You are attempting to perform a database reset. Type 'YES' to confirm or 'NO' to stop: " confirm

if [ "$confirm" != "YES" ]; then
    echo "Reset aborted."
    exit 1
fi

echo "Flushing database"
python manage.py flush --no-input --settings=adopt_a_tree.settings_azure

echo "Re-applying migrations"
python manage.py migrate --settings=adopt_a_tree.settings_azure

echo "Collecting static files"
python manage.py collectstatic --noinput --settings=adopt_a_tree.settings_azure