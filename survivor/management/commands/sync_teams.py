# survivor/management/commands/sync_teams.py
from django.core.management.base import BaseCommand
from survivor.models import Team
from survivor.services.football_api import FootballDataAPI, TeamMapper
import re

class Command(BaseCommand):
    help = 'Sync Bundesliga teams from football-data.org API'
    
    def handle(self, *args, **options):
        api = FootballDataAPI()
        
        self.stdout.write('Fetching teams from API...')
        api_teams = api.get_teams()
        
        if not api_teams:
            self.stdout.write(self.style.ERROR('Failed to fetch teams from API'))
            return
        
        created_count = 0
        updated_count = 0
        
        for api_team in api_teams:
            # Get team data from API
            api_name = api_team['name']
            short_name = api_team.get('tla', '')  # Three Letter Abbreviation
            crest_url = api_team.get('crest', '')
            
            # Map to our database name
            db_name = TeamMapper.get_team_name(api_name)
            
            # Extract primary color from crest or use defaults
            # This is simplified - you might want to manually set these
            colors = self._extract_colors(api_team)
            
            # Create or update team
            team, created = Team.objects.update_or_create(
                name=db_name,
                defaults={
                    'short_name': short_name[:3] if short_name else db_name[:3].upper(),
                    'color_primary': colors['primary'],
                    'color_secondary': colors['secondary'],
                }
            )
            
            if created:
                self.stdout.write(f'✓ Created team: {db_name}')
                created_count += 1
            else:
                self.stdout.write(f'✓ Updated team: {db_name}')
                updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSync complete! Created: {created_count}, Updated: {updated_count}'
            )
        )
        
        # List any teams in DB that weren't in API (might be relegated)
        api_team_names = [TeamMapper.get_team_name(t['name']) for t in api_teams]
        db_teams = Team.objects.all()
        
        for db_team in db_teams:
            if db_team.name not in api_team_names:
                self.stdout.write(
                    self.style.WARNING(f'⚠ Team in DB but not in API: {db_team.name}')
                )
    
    def _extract_colors(self, api_team):
        """Extract team colors - this is a simplified version"""
        # You might want to maintain a manual mapping of team colors
        # as the API doesn't provide them directly
        
        # Default colors based on common Bundesliga team colors
        team_colors = {
            'FC Bayern München': {'primary': '#DC052D', 'secondary': '#FFFFFF'},
            'Borussia Dortmund': {'primary': '#FDE100', 'secondary': '#000000'},
            'RB Leipzig': {'primary': '#DD0741', 'secondary': '#FFFFFF'},
            'Bayer 04 Leverkusen': {'primary': '#E32221', 'secondary': '#000000'},
            '1. FC Union Berlin': {'primary': '#EB1923', 'secondary': '#FFC947'},
            'Sport-Club Freiburg': {'primary': '#5B5B5B', 'secondary': '#FFFFFF'},
            'Eintracht Frankfurt': {'primary': '#E00005', 'secondary': '#000000'},
            'VfL Wolfsburg': {'primary': '#65B32E', 'secondary': '#FFFFFF'},
            '1. FSV Mainz 05': {'primary': '#C3141E', 'secondary': '#FFFFFF'},
            'Borussia Mönchengladbach': {'primary': '#000000', 'secondary': '#FFFFFF'},
            '1. FC Köln': {'primary': '#ED1C24', 'secondary': '#FFFFFF'},
            'TSG 1899 Hoffenheim': {'primary': '#1961B5', 'secondary': '#FFFFFF'},
            'SV Werder Bremen': {'primary': '#1D9053', 'secondary': '#FFFFFF'},
            'FC Augsburg': {'primary': '#BA3733', 'secondary': '#FFFFFF'},
            'VfB Stuttgart': {'primary': '#E32219', 'secondary': '#FFFFFF'},
            'VfL Bochum 1848': {'primary': '#005BA4', 'secondary': '#FFFFFF'},
            '1. FC Heidenheim 1846': {'primary': '#ED1C24', 'secondary': '#003D7C'},
            'SV Darmstadt 98': {'primary': '#004BA0', 'secondary': '#FFFFFF'},
        }
        
        api_name = api_team['name']
        return team_colors.get(api_name, {
            'primary': '#000000',
            'secondary': '#FFFFFF'
        })