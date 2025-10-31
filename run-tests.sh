#!/bin/bash

# Set Django settings module
export DJANGO_SETTINGS_MODULE=config.settings

# Run migrations first
python manage.py migrate --noinput

# Run tests with coverage (terminal report only)
python -m pytest --cov=api --cov-report=term-missing --cov-config=.coveragerc "$@"