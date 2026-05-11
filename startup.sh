#!/bin/bash

echo "Starting gunicorn server"
gunicorn --bind=0.0.0.0:8000 --workers 1 --timeout 120 adopt_a_tree.wsgi:application