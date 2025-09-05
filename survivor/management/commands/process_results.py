from django.core.management.base import BaseCommand
from django.db import transaction
from survivor.models import Match, Pick, PlayerEntry, Matchday

class Command(BaseCommand):
    help = 'Process match results and eliminate players who picked losing teams'

    def add_arguments(self, parser):
        parser.add_argument(
            '--matchday',
            type=int,
            help='Process specific matchday number'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true'
            help='Run wihthout making any changes'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        matchday_num = options.get('matchday')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved'))

        # Get unprocessed matches with results
        matches_query = Match.objects.filter(
            result__isnull=False,
            is_processed=False
        )

        if matchday_num:
            matches_query = matches_query.filter(matchday__number=matchday_num)
            self.stdout.write(f'Processing only matchday {matchday_num}')

        matches = matches_query.select_related('matchday', 'home_team', 'away_team')

        if not matches.exists():
            self.stdout.write(self.style.WARNING('No unprocessed matches with results found.'))
            return
        
        # Group matches by matchday
        matchdays = {}
        for match in matches:
            if match.matchday.number not in matchdays:
                matchdays[match.matchday] = []
            matchdays[match.matchday].append(match)

        # Process each matchday
        for matchday, matchday_matches in matchdays.items():
            self.stdout.write(f'\n{self.style.NOTICE(f"Processing Matchday {matchday.number}")}')
            self.process_matchday(matchday, matchday_matches, dry_run)

    def process_matchday(self, matchday, matches, dry_run):
        """Process all matches for a matchday and eliminate players"""

        # Get all teams that played in this matchday
        teams_in_matchday = set()
        for match in matches:
            teams_in_matchday.add(match.home_team)
            teams_in_matchday.add(match.away_team)

        # Get all picks for this matchday
        picks = Pick.objects.filter(
            matchday=matchday,
            is_successful__isnull=True # Only unprocessed picks
        ).select_related('player_entry__user', 'player_entry__pool', 'team')

        if not picks.exists():
            self.stdout.write('No picks to process for this matchday')
            return
        
        successful_picks = []
        failed_picks = []

        with transaction.atomic():
            for pick in picks:
                # Find the match this team played in
                team_match = None
                for match in matches:
                    if pick.team in [match.home_team, match.away_team]:
                        team_match = match
                        break

                if not team_match:
                    # Team didn't play this matchday (shouldn't happen)
                    self.stdout.write(
                        self.style.WARNING(
                            f'{pick.player_entry.user.username} picked {pick.team.name} which did not play in matchday {matchday.number}'
                        )
                    )
                    continue

                # Check if team didn't lose
                if team_match.team_did_not_lose(pick.team):
                    # Success - team won or drew
                    pick.is_successful = True
                    successful_picks.append(pick)

                    result_emoji = "✅"
                    if team_match.result == 'DRAW':
                        result_text = "drew"
                    elif (pick.team == team_match.home_team and team_match.result == 'HOME_WIN') or \
                         (pick.team == team_match.away_team and team_match.result == 'AWAY_WIN'):
                        result_text = "won"

                    self.stdout.write(
                        f' {result_emoji} {pick.player_entry.user.username} survived - '
                        f'{pick.team.name} {result_text} '
                        f'({team_match.home_score}-{team_match.away_score})'
                    )
                else:
                    # Failed - team lost
                    pick.is_successful = False
                    failed_picks.append(pick)

                    # Eliminate player
                    pick.player_entry.is_eliminated = True
                    pick.player_entry.eliminated_matchday = matchday

                    self.stdout.write(
                        self.style.ERROR(
                            f'  ❌ {pick.player_entry.user.username} eliminated - '
                            f'{pick.team.name} lost '
                            f'({team_match.home_score}-{team_match.away_score})'
                        )
                    )

                if not dry_run:
                    pick.save()
                    if pick.is_successful == False:
                        pick.player_entry.save()

            # Mark matches as processed
            if not dry_run:
                for match in matches:
                    match.is_processed = True
                    match.save()

            # Mark matchday as complete if all matches are done
            all_matches_complete = not matchday.matches.filter(result__isnull=True).exists()
            if all_matches_complete and not dry_run:
                matchday.is_complete = True
                matchday.save()

        # Print summary
        self.stdout.write(f'\n {self.style.SUCCESS("Summary for Matchday " + str(matchday.number))}')
        self.stdout.write(f'  Survived: {len(successful_picks)} players')
        self.stdout.write(f'  Eliminated: {len(failed_picks)} players')

        # Check for pool winneers
        for pool in set(pick.player_entry.pool for pick in picks):
            active_count = PlayerEntry.objects.filter(
                pool=pool,
                is_eliminated=False
            ).count()

            if active_count == 1:
                winner = PlayerEntry.objects.filter(
                    pool=pool,
                    is_eliminated=False
                ).first()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n 🏆 WINNER: {winner.user.username} wins {pool.name}!'
                    )
                )
            elif active_count == 0:
                self.stdout.write(
                    self.style.WARNING(
                        f'\n  🤝 NO SURVIVORS: Everyone eliminated in {pool.name}!'
                    )
                )