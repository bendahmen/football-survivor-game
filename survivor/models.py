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
    start_date = models.DateField()
    end_date = models.DateField()
    is_complete = models.BooleanField(default=False)

    class Meta:
        unique_together = ['season', 'number']
        ordering = ['number']

class Match(models.Model):
    RESULT_CHOICES = [
        ('HOME', 'Home Win'),
        ('AWAY', 'Away Win'),
        ('DRAW', 'Draw'),
        (None, 'Not Played')
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

    def save(self, *args, **kwargs):
        if self.home_score is not None and self.away_score is not None:
            if self.home_score > self.away_score:
                self.result = 'HOME'
            elif self.home_score < self.away_score:
                self.result = 'AWAY'
            else:
                self.result = 'DRAW'
        super().save(*args, **kwargs)

    def did_not_lose(self, team):
        if self.result is None:
            return False
        if team == self.home_team and self.result in ['HOME', 'DRAW']:
            return True
        if team == self.away_team and self.result in ['AWAY', 'DRAW']:
            return True
        return False
    
    def __str__(self):
        return f"{self.home_team} vs {self.away_team} on {self.kickoff.strftime('%Y-%m-%d')}"

class GamePool(models.Model):
    name = models.CharField(max_length=100)
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    start_date = models.DateField()
    is_active = models.BooleanField(default=True)

class PlayerEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pool = models.ForeignKey(GamePool, on_delete=models.CASCADE)
    is_eliminated = models.BooleanField(default=False)
    eliminated_matchday = models.ForeignKey(Matchday, null=True, blank=True, 
                                            on_delete=models.SET_NULL, 
                                            related_name='eliminations')

class Pick(models.Model):
    player_entry = models.ForeignKey(PlayerEntry, on_delete=models.CASCADE,
                                     related_name='picks')
    matchday = models.ForeignKey(Matchday, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    is_successful = models.BooleanField(null=True, blank=True)

    def clean(self):
        # Check if teams has already been picked twice
        pick_count = Pick.objects.filter(
            player_entry=self.player_entry,
            team=self.team
        ).exclude(pk=self.pk).count()

        if pick_count >= 2:
            raise ValidationError(f"You've already picked {self.team} twice!")
        
        # Check if pick deadline has passed
        pick_deadline = self.matchday.start_date
        if timezone.now() >= pick_deadline:
            raise ValidationError(f"The deadline for this matchday has passed!")
        
        # Check if player is eliminated
        if self.player_entry.eliminated:
            raise ValidationError("You are eliminated!")
        

