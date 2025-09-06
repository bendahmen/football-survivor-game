#!/usr/bin/env bash
# build.sh
# This script runs during deployment on Render

set -o errexit  # Exit on error

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate

# Create superuser if it doesn't exist
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'changeme123')
    print('Superuser created')
else:
    print('Superuser already exists')
END

# Load initial teams if not present
python manage.py shell << END
from survivor.models import Team
if Team.objects.count() < 18:
    from django.core.management import call_command
    call_command('load_teams')
    print('Teams loaded')
END

echo "Build completed successfully!"