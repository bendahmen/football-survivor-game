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

# Initial data sync - only on first deployment when no teams exist
python manage.py shell << END
from survivor.models import Team, Season
if Team.objects.count() == 0:
    print('No teams found - running initial data sync...')
    from django.core.management import call_command
    import os
    
    # Check if API key is set
    api_key = os.environ.get('FOOTBALL_DATA_API_KEY')
    
    if api_key:
        try:
            # Sync teams from API
            call_command('sync_teams')
            print('Teams synced from API')
            
            # Sync fixtures for current season
            call_command('sync_fixtures', season=2024)
            print('Fixtures synced for 2024/25 season')
            
            # Process any results
            call_command('process_results')
            print('Results processed')
        except Exception as e:
            print(f'Warning: Could not sync from API: {e}')
            print('Falling back to hardcoded teams...')
            try:
                call_command('load_teams')
                print('Loaded hardcoded teams as fallback')
            except Exception as e2:
                print(f'Could not load hardcoded teams: {e2}')
            print('You will need to manually sync fixtures using the admin dashboard at /survivor/admin/sync/')
    else:
        print('FOOTBALL_DATA_API_KEY not set - loading hardcoded teams')
        try:
            call_command('load_teams')
            print('Loaded hardcoded teams')
        except Exception as e:
            print(f'Could not load teams: {e}')
        print('Set FOOTBALL_DATA_API_KEY and use admin dashboard to sync fixtures')
else:
    print(f'Teams already exist ({Team.objects.count()} teams) - skipping initial sync')
END

echo "Build completed successfully!"