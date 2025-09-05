# survivor/management/commands/create_test_data.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta, datetime
from survivor.models import Season, Matchday, Match, Team, GamePool, PlayerEntry, Pick
import random

class Command(BaseCommand):
    help = 'Creates comprehensive test data for development'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Number of test users to create'
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Creating test data...')
        
        # Step 1: Create or get season
        season, created = Season.objects.get_or_create(
            year='2024-25',
            defaults={
                'is_active': True,
                'start_date': timezone.now().date(),
                'end_date': timezone.now().date() + timedelta(days=270)
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created season {season.year}'))
        else:
            self.stdout.write(f'Season {season.year} already exists')
        
        # Step 2: Get all teams (assuming load_teams was run)
        teams = list(Team.objects.all())
        if len(teams) < 18:
            self.stdout.write(self.style.ERROR('ERROR: Not enough teams! Run load_teams command first.'))
            return
        
        # Step 3: Create matchdays and matches
        self.create_matchdays_and_matches(season, teams)
        
        # Step 4: Create test users
        test_users = self.create_test_users(options['users'])
        
        # Step 5: Create game pools
        pools = self.create_game_pools(season, test_users[0] if test_users else None)
        
        # Step 6: Add players to pools and create some picks
        if pools and test_users:
            self.add_players_and_picks(pools[0], test_users, season)
        
        self.stdout.write(self.style.SUCCESS('\n✓ Test data creation complete!'))
        self.print_summary()
    
    def create_matchdays_and_matches(self, season, teams):
        """Create first 5 matchdays with matches"""
        for md_num in range(1, 6):
            # Calculate dates for matchday
            # First matchday starts in 3 days, then weekly
            if md_num == 1:
                start_date = timezone.now() + timedelta(days=3)
            else:
                start_date = timezone.now() + timedelta(days=3 + (7 * (md_num - 1)))
            
            end_date = start_date + timedelta(days=3)
            
            matchday, created = Matchday.objects.get_or_create(
                season=season,
                number=md_num,
                defaults={
                    'start_date': start_date,
                    'end_date': end_date,
                    'is_complete': False
                }
            )
            
            if created:
                # Shuffle teams for random matchups
                random.shuffle(teams)
                
                # Create 9 matches (18 teams, each plays once)
                for i in range(9):
                    # Vary kickoff times (Friday night, Saturday afternoon/evening, Sunday)
                    if i == 0:  # Friday night match
                        kickoff = start_date.replace(hour=20, minute=30)
                    elif i < 5:  # Saturday afternoon
                        kickoff = start_date + timedelta(days=1)
                        kickoff = kickoff.replace(hour=15, minute=30)
                    elif i < 8:  # Saturday evening
                        kickoff = start_date + timedelta(days=1)
                        kickoff = kickoff.replace(hour=18, minute=30)
                    else:  # Sunday afternoon
                        kickoff = start_date + timedelta(days=2)
                        kickoff = kickoff.replace(hour=17, minute=30)
                    
                    match = Match.objects.create(
                        matchday=matchday,
                        home_team=teams[i*2],
                        away_team=teams[i*2 + 1],
                        kickoff=kickoff
                    )
                
                self.stdout.write(f'✓ Created matchday {md_num} with 9 matches')
            else:
                self.stdout.write(f'Matchday {md_num} already exists')
        
        # Simulate results for past matchday (if first matchday is in the past)
        self.simulate_past_results(season)
    
    def simulate_past_results(self, season):
        """Add results to any matchdays that have passed"""
        past_matchdays = Matchday.objects.filter(
            season=season,
            end_date__lt=timezone.now(),
            is_complete=False
        )
        
        for matchday in past_matchdays:
            for match in matchday.matches.filter(result__isnull=True):
                # Simulate random scores
                home_score = random.randint(0, 4)
                away_score = random.randint(0, 4)
                
                # Slight home advantage
                if random.random() < 0.1:  # 10% chance to add home advantage
                    home_score += 1
                
                match.home_score = home_score
                match.away_score = away_score
                match.save()  # This will auto-calculate result in the model's save method
                
            matchday.is_complete = True
            matchday.save()
                            self.stdout.write(f'✓ Simulated results for matchday {matchday.number}')
    
    def create_test_users(self, num_users):
        """Create test users for the pool"""
        test_users = []
        
        for i in range(1, num_users + 1):
            username = f'player{i}'
            email = f'player{i}@test.com'
            password = 'testpass123'
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': f'Player',
                    'last_name': f'{i}'
                }
            )
            
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(f'✓ Created user: {username}')
                test_users.append(user)
            else:
                self.stdout.write(f'User {username} already exists')
                test_users.append(user)
        
        return test_users
    
    def create_game_pools(self, season, creator):
        """Create test game pools"""
        pools = []
        
        # Create main pool
        pool_data = [
            {'name': 'Main Pool 2024-25', 'entry_fee': 20.00},
            {'name': 'Free Pool', 'entry_fee': 0.00},
            {'name': 'High Stakes Pool', 'entry_fee': 100.00},
        ]
        
        # Use admin user or first test user as creator
        if not creator:
            creator = User.objects.filter(is_superuser=True).first()
            if not creator:
                creator = User.objects.first()
        
        for data in pool_data:
            pool, created = GamePool.objects.get_or_create(
                name=data['name'],
                season=season,
                defaults={
                    'created_by': creator,
                    'entry_fee': data['entry_fee'],
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(f"✓ Created pool: {pool.name}")
                pools.append(pool)
            else:
                self.stdout.write(f"Pool {pool.name} already exists")
                pools.append(pool)
        
        return pools
    
    def add_players_and_picks(self, pool, users, season):
        """Add players to pool and create some sample picks"""
        # Add all users to the pool
        for user in users:
            entry, created = PlayerEntry.objects.get_or_create(
                user=user,
                pool=pool
            )
            
            if created:
                self.stdout.write(f'✓ Added {user.username} to {pool.name}')
        
        # Get upcoming matchday for picks
        upcoming_matchday = Matchday.objects.filter(
            season=season,
            start_date__gt=timezone.now()
        ).order_by('number').first()
        
        if upcoming_matchday:
            # Create picks for some users
            teams = list(Team.objects.all())
            entries = PlayerEntry.objects.filter(pool=pool, is_eliminated=False)[:5]  # First 5 users make picks
            
            for entry in entries:
                # Pick a random team
                team = random.choice(teams)
                
                try:
                    pick, created = Pick.objects.get_or_create(
                        player_entry=entry,
                        matchday=upcoming_matchday,
                        defaults={'team': team}
                    )
                    
                    if created:
                        self.stdout.write(f'  → {entry.user.username} picked {team.short_name}')
                except ValidationError as e:
                    self.stdout.write(self.style.WARNING(f'  → Could not create pick: {e}'))
        
        # Simulate some eliminations from past matchdays
        past_matchday = Matchday.objects.filter(
            season=season,
            is_complete=True
        ).first()
        
        if past_matchday:
            # Eliminate 2 random players
            unlucky_entries = PlayerEntry.objects.filter(
                pool=pool,
                is_eliminated=False
            ).order_by('?')[:2]
            
            for entry in unlucky_entries:
                entry.is_eliminated = True
                entry.eliminated_matchday = past_matchday
                entry.save()
                self.stdout.write(f'  → Simulated elimination: {entry.user.username} in matchday {past_matchday.number}')
    
    def print_summary(self):
        """Print summary of created data"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('TEST DATA SUMMARY:'))
        self.stdout.write('='*50)
        
        self.stdout.write(f'• Active Season: {Season.objects.filter(is_active=True).first()}')
        self.stdout.write(f'• Total Teams: {Team.objects.count()}')
        self.stdout.write(f'• Total Matchdays: {Matchday.objects.count()}')
        self.stdout.write(f'• Total Matches: {Match.objects.count()}')
        self.stdout.write(f'• Total Pools: {GamePool.objects.count()}')
        self.stdout.write(f'• Total Users: {User.objects.filter(username__startswith="player").count()}')
        self.stdout.write(f'• Total Player Entries: {PlayerEntry.objects.count()}')
        self.stdout.write(f'• Total Picks: {Pick.objects.count()}')
        
        self.stdout.write('\n' + self.style.WARNING('TEST USER CREDENTIALS:'))
        self.stdout.write('Username: player1 to player10')
        self.stdout.write('Password: testpass123')
        self.stdout.write('\nAdmin access via: /admin/')
        self.stdout.write('='*50)