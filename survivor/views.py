from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from .models import GamePool, PlayerEntry, Pick, Matchday, Team, Season

def home(request):
    active_pools = GamePool.objects.filter(is_active=True).select_related('season')
    context = {
        'active_pools': active_pools
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

    context = {
        'pool': pool,
        'player_entry': player_entry,
        'current_matchday': current_matchday,
        'next_matchday': next_matchday,
        'all_entries': all_entries
    }

    # If player is in pool and not eliminated, get pick info
    if player_entry and not player_entry.is_eliminated and next_matchday:
        # Get teams already picked by count
        picked_teams = {}
        for pick in player_entry.picks.all():
            if pick.team.id not in picked_teams:
                picked_teams[pick.team.id] = 0
            picked_teams[pick.team.id] += 1

        # Get all teams with pick availability
        teams = []
        for team in Team.objects.all().order_by('name'):
            teams.append({
                'team': team,
                'picked_count': picked_teams.get(team.id, 0),
                'available': picked_teams.get(team.id, 0) < 2
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
def create_pool(request):
    # Implementation for creating a new pool
    # This would typically have a form
    pass