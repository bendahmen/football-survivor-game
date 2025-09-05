from django.core.management.base import BaseCommand
from survivor.models import Team

class Command(BaseCommand):
    help = 'Load Bundesliga teams'

    def handle(self, *args, **options):
        teams = [
            {'name': 'Bayern Munich', 'short_name': 'FCB', 'color_primary': '#DC052D'},
            {'name': 'Borussia Dortmund', 'short_name': 'BVB', 'color_primary': '#FDE100'},
            {'name': 'RB Leipzig', 'short_name': 'RBL', 'color_primary': '#DD0741'},
            {'name': 'Bayer Leverkusen', 'short_name': 'B04', 'color_primary': '#E32221'},
            {'name': 'Union Berlin', 'short_name': 'FCU', 'color_primary': '#EB1923'},
            {'name': 'SC Freiburg', 'short_name': 'SCF', 'color_primary': '#5B5B5B'},
            {'name': 'Eintracht Frankfurt', 'short_name': 'SGE', 'color_primary': '#E00005'},
            {'name': 'VfL Wolfsburg', 'short_name': 'WOB', 'color_primary': '#65B32E'},
            {'name': 'Mainz 05', 'short_name': 'M05', 'color_primary': '#C3141E'},
            {'name': 'Borussia Mönchengladbach', 'short_name': 'BMG', 'color_primary': '#000000'},
            {'name': 'FC Köln', 'short_name': 'KOE', 'color_primary': '#ED1C24'},
            {'name': 'Hoffenheim', 'short_name': 'TSG', 'color_primary': '#1961B5'},
            {'name': 'Werder Bremen', 'short_name': 'SVW', 'color_primary': '#1D9053'},
            {'name': 'FC Augsburg', 'short_name': 'FCA', 'color_primary': '#BA3733'},
            {'name': 'VfB Stuttgart', 'short_name': 'VFB', 'color_primary': '#E32219'},
            {'name': 'VfL Bochum', 'short_name': 'BOC', 'color_primary': '#005BA4'},
            {'name': 'FC Heidenheim', 'short_name': 'FCH', 'color_primary': '#ED1C24'},
            {'name': 'SV Darmstadt 98', 'short_name': 'D98', 'color_primary': '#004BA0'},
        ]

        for team_data in teams:
            team, created = Team.objects.get_or_create(
                name=team_data['name'],
                defaults={
                    'short_name': team_data['short_name'],
                    'color_primary': team_data['color_primary'],
                    'color_secondary': '#FFFFFF' if team_data['color_primary'] != '#FFFFFF' else '#000000',
                }
            )
            if created:
                self.stdout.write(f"Created team: {team.name}")
            else:
                self.stdout.write(f"Team already exists: {team.name}")