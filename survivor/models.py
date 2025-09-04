from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

class Team(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=3)
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name

class Season(models.Model):
    year = models.CharField(max_length=7, unique=True) # e.g. "2024-25"
    is_active = models.BooleanField(default=False)

    # Ensure only one active season at a time
    def save(self, *args, **kwargs):
        if self.is_active:
            Season.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

class Matchday(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
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

    matchday = models.ForeignKey(Matchday, on_delete=models.CASCADE)
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')
    kickoff = models.DateTimeField()
    result = models.CharField(max_length=4, choices=RESULT_CHOICES, null=True, blank=True)
    score = models.CharField(max_length=5, null=True, blank=True) # e.g. "15:10"

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

class PlayerEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pool = models.ForeignKey(GamePool, on_delete=models.CASCADE)
    eliminated = models.BooleanField(default=False)
    elimination_date = models.DateField(null=True, blank=True)