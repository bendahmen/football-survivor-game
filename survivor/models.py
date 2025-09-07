from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    short_name = models.CharField(max_length=3)
    color_primary = models.CharField(max_length=7, default='#FFFFFF') # Hex color
    color_secondary = models.CharField(max_length=7, default='#000000') # Hex color

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Season(models.Model):
    year = models.CharField(max_length=7, unique=True) # e.g. "2024-25"
    is_active = models.BooleanField(default=False)
    start_date = models.DateField()
    end_date = models.DateField()

    # Ensure only one active season at a time
    def save(self, *args, **kwargs):
        if self.is_active:
            Season.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Season {self.year}"

class Matchday(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE,
                               related_name ='matchdays')
    number = models.PositiveIntegerField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_complete = models.BooleanField(default=False)

    class Meta:
        unique_together = ['season', 'number']
        ordering = ['number']

    def __str__(self):
        return f"Matchday {self.number} - {self.season.year}"
    
    @property
    def has_started(self):
        return timezone.now() >= self.start_date
    
    @property
    def is_current(self):
        now = timezone.now().date()
        return self.start_date <= now <= self.end_date

class Match(models.Model):
    RESULT_CHOICES = [
        ('HOME', 'Home Win'),
        ('AWAY', 'Away Win'),
        ('DRAW', 'Draw')
    ]

    matchday = models.ForeignKey(Matchday, on_delete=models.CASCADE,
                                 related_name='matches')
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')
    kickoff = models.DateTimeField()
    result = models.CharField(max_length=4, choices=RESULT_CHOICES, null=True, blank=True)
    home_score = models.IntegerField(null=True, blank=True)
    away_score = models.IntegerField(null=True, blank=True)
    is_processed = models.BooleanField(default=False)
    modified_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto-calculate result from scores
        if self.home_score is not None and self.away_score is not None:
            if self.home_score > self.away_score:
                self.result = 'HOME'
            elif self.home_score < self.away_score:
                self.result = 'AWAY'
            else:
                self.result = 'DRAW'
        super().save(*args, **kwargs)

    def did_not_lose(self, team):
        """Check if the given team did not lose this match"""
        if self.result is None:
            return None  # Match not played yet
        
        if team == self.home_team:
            return self.result in ['HOME', 'DRAW']
        elif team == self.away_team:
            return self.result in ['AWAY', 'DRAW']
        else:
            return None  # Team not in this match
    
    def __str__(self):
        return f"{self.home_team.short_name} vs {self.away_team.short_name} on {self.kickoff.strftime('%Y-%m-%d')}"

class GamePool(models.Model):
    name = models.CharField(max_length=100)
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='pools')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_pools')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    deadline = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.season.year})"
    
    @property
    def is_open(self):
        return self.is_active and timezone.now() < self.deadline
    
    @property
    def active_players_count(self):
        return self.entries.filter(is_eliminated=False).count()
    
    @property
    def total_players_count(self):
        return self.entries.count()

class PlayerEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pool = models.ForeignKey(GamePool, on_delete=models.CASCADE, related_name='entries')
    is_eliminated = models.BooleanField(default=False)
    eliminated_matchday = models.ForeignKey(Matchday, null=True, blank=True, 
                                            on_delete=models.SET_NULL, 
                                            related_name='eliminations')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'pool']
        ordering = ['is_eliminated', '-eliminated_matchday__number', 'user__username']

    def __str__(self):
        status = "Eliminated" if self.is_eliminated else "Active"
        return f"{self.user.username} - {self.pool.name} ({status})"
    
    def get_pick_count_for_team(self, team):
        """Get how many times the player has picked a specific team"""
        return (self.picks.filter(team=team).count())
    
    def can_pick_team(self, team):
        """Check if the player can pick the given team (not picked twice already)"""
        return self.get_pick_count_for_team(team) < 2
    
    def get_available_teams(self, matchday=None):
        """Get list of teams that can still be picked by this player"""
        teams = Team.objects.all()
        available = []
        for team in teams:
            if self.can_pick_team(team):
                available.append(team)
        return available

    def clean(self):
        # Ensure that a player can only join a GamePool if it is open
        if not self.pool.is_open:
            raise ValidationError('Cannot join pool: The deadline has passed.')

    def save(self, *args, **kwargs):
        # Run validation before saving
        self.full_clean()
        super().save(*args, **kwargs)

class Pick(models.Model):
    player_entry = models.ForeignKey(PlayerEntry, on_delete=models.CASCADE,
                                     related_name='picks')
    matchday = models.ForeignKey(Matchday, on_delete=models.CASCADE, related_name='picks')
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    is_successful = models.BooleanField(null=True, blank=True)

    class Meta:
        unique_together = ['player_entry', 'matchday']
        ordering = ['matchday__number']

    def __str__(self):
        return f"{self.player_entry.user.username} picked {self.team.short_name} for Matchday {self.matchday.number}"

    def clean(self):
        """Validate the pick before saving"""
        # Check if teams has already been picked twice
        if self.player_entry and self.team:
            pick_count = Pick.objects.filter(
                player_entry=self.player_entry,
                team=self.team
            ).exclude(pk=self.pk).count()

            if pick_count >= 2:
                raise ValidationError(f"You've already picked {self.team} twice!")
        
        # Check if pick deadline has passed
        if self.matchday and self.matchday.has_started:
            raise ValidationError("Pick deadline has passed for this matchday!")
        
        # Check if player is eliminated
        if self.player_entry and self.player_entry.is_eliminated:
            raise ValidationError("You are eliminated!")
        
    def save(self, *args, **kwargs):
        # Run validation before saving
        self.full_clean()
        super().save(*args, **kwargs)

