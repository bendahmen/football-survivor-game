from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Prefetch
from datetime import timedelta
from .models import GamePool, PlayerEntry, Pick, Matchday, Team, Season, Match

def home(request):
    active_pools = GamePool.objects.filter(is_active=True).select_related('season')
    
    # Get upcoming matches for preview
    upcoming_matches = Match.objects.filter(
        kickoff__gte=timezone.now(),
        result__isnull=True
    ).select_related('home_team', 'away_team', 'matchday').order_by('kickoff')[:5]
    
    context = {
        'active_pools': active_pools,
        'upcoming_matches': upcoming_matches
    }
    return render(request, 'home.html', context)

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

@login_required
def pool_detail(request, pool_id):
    pool = get_object_or_404(GamePool, id=pool_id)

    # Check if user is in this pool
    try:
        player_entry = PlayerEntry.objects.get(user=request.user, pool=pool)
    except PlayerEntry.DoesNotExist:
        player_entry = None

    # Get current matchday
    current_matchday = Matchday.objects.filter(
        season=pool.season,
        start_date__lte=timezone.now()
    ).order_by('-number').first()

    # Get next matchday for picks
    next_matchday = Matchday.objects.filter(
        season=pool.season,
        start_date__gt=timezone.now()
    ).order_by('number').first()

    # Get all players in pool
    all_entries = PlayerEntry.objects.filter(
        pool=pool
    ).select_related('user').order_by('is_eliminated', '-eliminated_matchday__number')

    # Get fixtures for next matchday
    next_fixtures = []
    if next_matchday:
        next_fixtures = Match.objects.filter(
            matchday=next_matchday
        ).select_related('home_team', 'away_team').order_by('kickoff')
    
    # Get recent results from current/last matchday
    recent_results = []
    if current_matchday:
        recent_results = Match.objects.filter(
            matchday=current_matchday,
            result__isnull=False
        ).select_related('home_team', 'away_team').order_by('-kickoff')[:9]

    context = {
        'pool': pool,
        'player_entry': player_entry,
        'current_matchday': current_matchday,
        'next_matchday': next_matchday,
        'all_entries': all_entries,
        'next_fixtures': next_fixtures,
        'recent_results': recent_results
    }

    # If player is in pool and not eliminated, get pick info
    if player_entry and not player_entry.is_eliminated and next_matchday:
        # Get teams already picked by count
        picked_teams = {}
        for pick in player_entry.picks.all():
            if pick.team.id not in picked_teams:
                picked_teams[pick.team.id] = 0
            picked_teams[pick.team.id] += 1

        # Get all teams with pick availability and their fixtures
        teams = []
        for team in Team.objects.all().order_by('name'):
            # Find this team's match in the next matchday
            team_match = None
            for fixture in next_fixtures:
                if team in [fixture.home_team, fixture.away_team]:
                    team_match = fixture
                    break
            
            teams.append({
                'team': team,
                'pick_count': picked_teams.get(team.id, 0),
                'available': picked_teams.get(team.id, 0) < 2,
                'match': team_match,  # Add match info to each team
                'is_home': team_match.home_team == team if team_match else None
            })

        # Check if already picked for this matchday
        current_pick = Pick.objects.filter(
            player_entry=player_entry,
            matchday=next_matchday
        ).first()

        context['teams'] = teams
        context['current_pick'] = current_pick

    return render(request, 'pool_detail.html', context)

@login_required
def fixtures(request, pool_id=None):
    """Display fixtures and results for all matchdays"""
    
    # Get active season
    season = Season.objects.filter(is_active=True).first()
    if not season:
        messages.warning(request, 'No active season found.')
        return redirect('home')
    
    # Get pool if specified
    pool = None
    if pool_id:
        pool = get_object_or_404(GamePool, id=pool_id)
        season = pool.season
    
    # Get all matchdays with their matches
    matchdays = Matchday.objects.filter(
        season=season
    ).prefetch_related(
        Prefetch(
            'matches',
            queryset=Match.objects.select_related('home_team', 'away_team').order_by('kickoff')
        )
    ).order_by('number')
    
    # Categorize matchdays
    past_matchdays = []
    current_matchday = None
    future_matchdays = []
    
    now = timezone.now()
    for md in matchdays:
        if md.end_date < now:
            past_matchdays.append(md)
        elif md.start_date <= now <= md.end_date:
            current_matchday = md
        else:
            future_matchdays.append(md)
    
    context = {
        'season': season,
        'pool': pool,
        'past_matchdays': past_matchdays,
        'current_matchday': current_matchday,
        'future_matchdays': future_matchdays,
        'all_matchdays': matchdays
    }
    
    return render(request, 'fixtures.html', context)

def matchday_fixtures(request, matchday_id):
    """Display detailed fixtures for a specific matchday"""
    matchday = get_object_or_404(Matchday, id=matchday_id)
    
    matches = Match.objects.filter(
        matchday=matchday
    ).select_related('home_team', 'away_team').order_by('kickoff')
    
    # Get pick statistics for each team
    team_picks = {}
    if request.user.is_authenticated:
        picks = Pick.objects.filter(
            matchday=matchday
        ).values('team').annotate(count=Count('id'))
        
        for pick in picks:
            team_picks[pick['team']] = pick['count']
    
    # Add pick counts to matches
    matches_with_stats = []
    for match in matches:
        matches_with_stats.append({
            'match': match,
            'home_picks': team_picks.get(match.home_team.id, 0),
            'away_picks': team_picks.get(match.away_team.id, 0)
        })
    
    context = {
        'matchday': matchday,
        'matches_with_stats': matches_with_stats,
        'total_picks': sum(team_picks.values())
    }
    
    return render(request, 'matchday_fixtures.html', context)

@login_required
def join_pool(request, pool_id):
    pool = get_object_or_404(GamePool, id=pool_id)

    # Check if user already in pool
    if PlayerEntry.objects.filter(user=request.user, pool=pool).exists():
        messages.warning(request, 'You are already in this pool.')
    else:
        PlayerEntry.objects.create(user=request.user, pool=pool)
        messages.success(request, f'Successfully joined pool {pool.name}!')

    return redirect('survivor:pool_detail', pool_id=pool.id)

@login_required
def make_pick(request, pool_id):
    if request.method == 'POST':
        pool = get_object_or_404(GamePool, id=pool_id)
        player_entry = get_object_or_404(PlayerEntry, user=request.user, pool=pool)
        
        if player_entry.is_eliminated:
            messages.error(request, 'You have been eliminated from this pool!')
            return redirect('survivor:pool_detail', pool_id=pool.id)
        
        matchday_id = request.POST.get('matchday_id')
        team_id = request.POST.get('team_id')
        
        matchday = get_object_or_404(Matchday, id=matchday_id)
        team = get_object_or_404(Team, id=team_id)
        
        # Check if matchday has started
        if matchday.has_started:
            messages.error(request, 'This matchday has already started!')
            return redirect('survivor:pool_detail', pool_id=pool.id)
        
        # Check if team can be picked
        if not player_entry.can_pick_team(team):
            messages.error(request, f'You have already picked {team.name} twice!')
            return redirect('survivor:pool_detail', pool_id=pool.id)
        
        # Create or update pick
        pick, created = Pick.objects.update_or_create(
            player_entry=player_entry,
            matchday=matchday,
            defaults={'team': team}
        )
        
        if created:
            messages.success(request, f'Pick saved: {team.name} for Matchday {matchday.number}')
        else:
            messages.success(request, f'Pick updated: {team.name} for Matchday {matchday.number}')
    
    return redirect('survivor:pool_detail', pool_id=pool_id)

@login_required
def pick_history(request, pool_id):
    """Display user's pick history for a pool"""
    pool = get_object_or_404(GamePool, id=pool_id)
    
    try:
        player_entry = PlayerEntry.objects.get(user=request.user, pool=pool)
    except PlayerEntry.DoesNotExist:
        messages.warning(request, 'You are not in this pool.')
        return redirect('survivor:pool_detail', pool_id=pool.id)
    
    picks = Pick.objects.filter(
        player_entry=player_entry
    ).select_related('team', 'matchday').order_by('matchday__number')
    
    # Get the match each team played
    picks_with_matches = []
    for pick in picks:
        match = Match.objects.filter(
            Q(home_team=pick.team) | Q(away_team=pick.team),
            matchday=pick.matchday
        ).select_related('home_team', 'away_team').first()
        
        picks_with_matches.append({
            'pick': pick,
            'match': match,
            'opponent': match.away_team if match and match.home_team == pick.team else match.home_team if match else None,
            'was_home': match.home_team == pick.team if match else None
        })
    
    context = {
        'pool': pool,
        'player_entry': player_entry,
        'picks_with_matches': picks_with_matches
    }
    
    return render(request, 'pick_history.html', context)

@login_required
def create_pool(request):
    # Implementation for creating a new pool
    # This would typically have a form
    pass