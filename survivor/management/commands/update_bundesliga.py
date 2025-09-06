# survivor/management/commands/update_bundesliga.py
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update all Bundesliga data (teams, fixtures, results)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--full',
            action='store_true',
            help='Full sync of all data (teams + all fixtures)'
        )
        parser.add_argument(
            '--season',
            type=int,
            default=2024,
            help='Season year to sync (default: 2024)'
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Starting Bundesliga data update...\n')
        
        try:
            # Always sync teams first
            self.stdout.write('Step 1: Syncing teams...')
            call_command('sync_teams')
            self.stdout.write(self.style.SUCCESS('✓ Teams synced\n'))
            
            # Sync fixtures
            if options['full']:
                self.stdout.write(f'Step 2: Full sync of fixtures for {options["season"]} season...')
                call_command('sync_fixtures', season=options['season'])
            else:
                # Just sync current and next matchday
                self.stdout.write('Step 2: Syncing recent fixtures...')
                call_command('sync_fixtures', season=options['season'], results_only=True)
            
            self.stdout.write(self.style.SUCCESS('✓ Fixtures synced\n'))
            
            # Process results
            self.stdout.write('Step 3: Processing results...')
            call_command('process_results')
            self.stdout.write(self.style.SUCCESS('✓ Results processed\n'))
            
            self.stdout.write(
                self.style.SUCCESS('\n✅ Bundesliga data update complete!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Error during update: {str(e)}')
            )
            logger.error(f"Update failed: {e}", exc_info=True)
            raise
