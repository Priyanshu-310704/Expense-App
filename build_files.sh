#!/bin/bash
# Install backend dependencies
python3.12 -m pip install -r backend/requirements.txt

# Run migrations and collect static files
python3.12 backend/manage.py migrate --noinput
python3.12 backend/manage.py collectstatic --noinput --clear
