# survivor/management/commands/sync_fixtures.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from survivor.models import Season, Matchday, Match, Team
from survivor.services.football_api import FootballDataAPI, TeamMapper
import pytz

class Command(BaseCommand):
    help = 'Sync Bundesliga fixtures and results from football-data.org API'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--season',
            type=int,
            help='Specific season year to sync (e.g., 2024)'
        )
        parser.add_argument(
            '--matchday',
            type=int,
            help='Specific matchday to sync'
        )
        parser.add_argument(
            '--results-only',
            action='store_true',
            help='Only update results for existing matches'
        )
    
    def handle(self, *args, **options):
        api = FootballDataAPI()
        
        # Get current season from API if not specified
        if not options['season']:
            self.stdout.write('Fetching current season info...')
            season_data = api.get_current_season()
            if not season_data:
                self.stdout.write(self.style.ERROR('Failed to fetch season info'))
                return
            season_year = season_data['startDate'][:4]
        else:
            season_year = str(options['season'])
        
        # Create or get season in our database
        season = self._ensure_season_exists(season_year)
        
        # Fetch matches from API
        self.stdout.write(f'Fetching matches for season {season_year}...')
        api_matches = api.get_matches(season=season_year, matchday=options.get('matchday'))
        
        if not api_matches:
            self.stdout.write(self.style.ERROR('Failed to fetch matches from API'))
            return
        
        # Group matches by matchday
        matches_by_matchday = {}
        for match in api_matches:
            md_num = match['matchday']
            if md_num not in matches_by_matchday:
                matches_by_matchday[md_num] = []
            matches_by_matchday[md_num].append(match)
        
        # Process each matchday
        for matchday_num, matches in matches_by_matchday.items():
            if options.get('matchday') and matchday_num != options['matchday']:
                continue
            
            self._process_matchday(season, matchday_num, matches, options.get('results_only', False))
        
        self.stdout.write(self.style.SUCCESS('\n✓ Sync complete!'))
    
    def _ensure_season_exists(self, year):
        """Create or get season"""
        # Format season year (e.g., "2024" becomes "2024-25")
        start_year = int(year)
        end_year = start_year + 1
        season_str = f"{start_year}-{str(end_year)[2:]}"
        
        season, created = Season.objects.get_or_create(
            year=season_str,
            defaults={
                'start_date': datetime(start_year, 8, 1).date(),  # August
                'end_date': datetime(end_year, 5, 31).date(),  # May
                'is_active': True  # You might want to check if this is current season
            }
        )
        
        if created:
            self.stdout.write(f'✓ Created season: {season_str}')
        
        return season
    
    def _process_matchday(self, season, matchday_num, matches, results_only=False):
        """Process matches for a matchday"""
        
        if not matches:
            return
        
        # Get matchday dates from matches
        match_dates = [datetime.fromisoformat(m['utcDate'].replace('Z', '+00:00')) for m in matches]
        start_date = min(match_dates)
        end_date = max(match_dates) + timedelta(days=1)  # Add a day for buffer
        
        # Create or get matchday
        if not results_only:
            matchday, created = Matchday.objects.update_or_create(
                season=season,
                number=matchday_num,
                defaults={
                    'start_date': start_date,
                    'end_date': end_date,
                    'is_complete': all(m['status'] == 'FINISHED' for m in matches)
                }
            )
            
            if created:
                self.stdout.write(f'\n✓ Created Matchday {matchday_num}')
            else:
                self.stdout.write(f'\n✓ Updating Matchday {matchday_num}')
        else:
            try:
                matchday = Matchday.objects.get(season=season, number=matchday_num)
            except Matchday.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Matchday {matchday_num} not found'))
                return
        
        # Process each match
        created_count = 0
        updated_count = 0
        
        for api_match in matches:
            result = self._process_match(matchday, api_match, results_only)
            if result == 'created':
                created_count += 1
            elif result == 'updated':
                updated_count += 1
        
        self.stdout.write(
            f'  → Matchday {matchday_num}: '
            f'Created {created_count}, Updated {updated_count} matches'
        )
        
        # Update matchday completion status
        if all(m['status'] == 'FINISHED' for m in matches):
            matchday.is_complete = True
            matchday.save()
    
    def _process_match(self, matchday, api_match, results_only=False):
        """Process a single match"""
        
        # Get team names and map to our database
        home_team_name = TeamMapper.get_team_name(api_match['homeTeam']['name'])
        away_team_name = TeamMapper.get_team_name(api_match['awayTeam']['name'])
        
        # Get teams from database
        try:
            home_team = Team.objects.get(name=home_team_name)
            away_team = Team.objects.get(name=away_team_name)
        except Team.DoesNotExist as e:
            self.stdout.write(
                self.style.WARNING(
                    f'  ⚠ Team not found: {home_team_name} or {away_team_name}'
                )
            )
            return None
        
        # Parse match datetime
        kickoff = datetime.fromisoformat(api_match['utcDate'].replace('Z', '+00:00'))
        
        # Get scores and result
        score = api_match.get('score', {})
        full_time = score.get('fullTime', {})
        home_score = full_time.get('home')
        away_score = full_time.get('away')
        
        # Determine result
        result = None
        if home_score is not None and away_score is not None:
            if home_score > away_score:
                result = 'HOME'
            elif away_score > home_score:
                result = 'AWAY'
            else:
                result = 'DRAW'
        
        if results_only:
            # Only update existing matches
            try:
                match = Match.objects.get(
                    matchday=matchday,
                    home_team=home_team,
                    away_team=away_team
                )
                
                # Only update if match is finished
                if api_match['status'] == 'FINISHED':
                    match.home_score = home_score
                    match.away_score = away_score
                    match.result = result
                    match.save()
                    
                    self.stdout.write(
                        f'  ✓ Updated result: {home_team.short_name} {home_score}-{away_score} {away_team.short_name}'
                    )
                    return 'updated'
                    
            except Match.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠ Match not found: {home_team.name} vs {away_team.name}'
                    )
                )
                return None
        else:
            # Create or update match
            match, created = Match.objects.update_or_create(
                matchday=matchday,
                home_team=home_team,
                away_team=away_team,
                defaults={
                    'kickoff': kickoff,
                    'home_score': home_score,
                    'away_score': away_score,
                    'result': result,
                    'is_processed': False  # Will be processed by process_results command
                }
            )
            
            if created:
                self.stdout.write(
                    f'  ✓ Created: {home_team.short_name} vs {away_team.short_name} '
                    f'({kickoff.strftime("%Y-%m-%d %H:%M")})'
                )
                return 'created'
            else:
                if match.home_score != home_score or match.away_score != away_score:
                    self.stdout.write(
                        f'  ✓ Updated: {home_team.short_name} {home_score or "?"}-'
                        f'{away_score or "?"} {away_team.short_name}'
                    )
                return 'updated'
        
        return None