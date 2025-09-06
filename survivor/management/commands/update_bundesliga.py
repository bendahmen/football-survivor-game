# survivor/management/commands/update_bundesliga.py
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
from datetime import datetime, timedelta
from survivor.models import Matchday, Match

class Command(BaseCommand):
    help = 'Update Bundesliga fixtures and process results for survivor pools'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--full',
            action='store_true',
            help='Full sync of all fixtures (not just recent)'
        )
        parser.add_argument(
            '--no-process',
            action='store_true',
            help='Skip processing survivor pool results'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('='*50))
        self.stdout.write(self.style.NOTICE('BUNDESLIGA DATA UPDATE'))
        self.stdout.write(self.style.NOTICE('='*50))
        
        # Step 1: Sync teams (only if needed)
        self.stdout.write('\n📋 Checking teams...')
        from survivor.models import Team
        if Team.objects.count() < 18:
            self.stdout.write('Syncing teams from API...')
            call_command('sync_teams')
        else:
            self.stdout.write('Teams already loaded ✓')
        
        # Step 2: Sync fixtures
        self.stdout.write('\n📅 Updating fixtures and results...')
        
        if options['full']:
            # Full sync of entire season
            call_command('sync_fixtures')
        else:
            # Smart sync - only recent and upcoming matchdays
            self._smart_sync()
        
        # Step 3: Process survivor pool results
        if not options['no_process']:
            self.stdout.write('\n🎯 Processing survivor pool results...')
            
            # Find unprocessed matches with results
            unprocessed = Match.objects.filter(
                result__isnull=False,
                is_processed=False
            ).select_related('matchday')
            
            if unprocessed.exists():
                matchdays = set(m.matchday.number for m in unprocessed)
                self.stdout.write(
                    f'Found results for matchdays: {sorted(matchdays)}'
                )
                
                # Process results
                call_command('process_results')
            else:
                self.stdout.write('No new results to process ✓')
        
        # Step 4: Show summary
        self._show_summary()
        
        self.stdout.write(self.style.SUCCESS('\n✅ Update complete!'))
    
    def _smart_sync(self):
        """Smart sync - only sync relevant matchdays"""
        from survivor.models import Season, Matchday
        
        # Get active season
        try:
            season = Season.objects.get(is_active=True)
        except Season.DoesNotExist:
            self.stdout.write('No active season, doing full sync...')
            call_command('sync_fixtures')
            return
        
        now = timezone.now()
        
        # Find matchdays to sync:
        # 1. Current matchday (if any)
        current = Matchday.objects.filter(
            season=season,
            start_date__lte=now,
            end_date__gte=now
        ).first()
        
        # 2. Recently completed (last 2 matchdays)
        recent = Matchday.objects.filter(
            season=season,
            end_date__lt=now,
            end_date__gte=now - timedelta(days=14)
        ).order_by('-number')[:2]
        
        # 3. Upcoming (next 2 matchdays)
        upcoming = Matchday.objects.filter(
            season=season,
            start_date__gt=now,
            start_date__lte=now + timedelta(days=14)
        ).order_by('number')[:2]
        
        matchdays_to_sync = set()
        
        if current:
            matchdays_to_sync.add(current.number)
            self.stdout.write(f'Current matchday: {current.number}')
        
        for md in recent:
            matchdays_to_sync.add(md.number)
        if recent:
            self.stdout.write(f'Recent matchdays: {[md.number for md in recent]}')
        
        for md in upcoming:
            matchdays_to_sync.add(md.number)
        if upcoming:
            self.stdout.write(f'Upcoming matchdays: {[md.number for md in upcoming]}')
        
        # Sync each matchday
        for matchday_num in sorted(matchdays_to_sync):
            self.stdout.write(f'\nSyncing matchday {matchday_num}...')
            call_command('sync_fixtures', matchday=matchday_num)
    
    def _show_summary(self):
        """Show current state summary"""
        from survivor.models import Season, GamePool, PlayerEntry, Match
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write('CURRENT STATUS:')
        self.stdout.write('='*50)
        
        # Active season
        try:
            season = Season.objects.get(is_active=True)
            self.stdout.write(f'Season: {season.year}')
            
            # Current matchday
            now = timezone.now()
            current_md = Matchday.objects.filter(
                season=season,
                start_date__lte=now,
                end_date__gte=now
            ).first()
            
            if current_md:
                self.stdout.write(f'Current Matchday: {current_md.number}')
                
                # Matches today
                today_matches = Match.objects.filter(
                    matchday=current_md,
                    kickoff__date=now.date()
                ).count()
                if today_matches:
                    self.stdout.write(
                        self.style.WARNING(f'⚽ {today_matches} matches today!')
                    )
            
            # Next matchday
            next_md = Matchday.objects.filter(
                season=season,
                start_date__gt=now
            ).order_by('number').first()
            
            if next_md:
                days_until = (next_md.start_date - now).days
                self.stdout.write(
                    f'Next Matchday: {next_md.number} '
                    f'(in {days_until} days)'
                )
            
            # Pool status
            active_pools = GamePool.objects.filter(is_active=True).count()
            active_players = PlayerEntry.objects.filter(
                is_eliminated=False,
                pool__is_active=True
            ).count()
            
            self.stdout.write(f'\nActive Pools: {active_pools}')
            self.stdout.write(f'Active Players: {active_players}')
            
        except Season.DoesNotExist:
            self.stdout.write(self.style.WARNING('No active season'))