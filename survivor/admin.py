from django.contrib import admin
from .models import Team, Season, Matchday, Match, GamePool, PlayerEntry, Pick

# Register your models here.
@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'code')
    search_fields = ('name', 'short_name')

@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ['year', 'is_active', 'start_date', 'end_date']
    list_filter = ['is_active']

@admin.register(Matchday)
class MatchdayAdmin(admin.ModelAdmin):
    list_display = ['number', 'season', 'start_date', 'end_date', 'is_complete']
    list_filter = ['season', 'is_complete']
    ordering = ['season', 'number']


