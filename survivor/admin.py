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

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['matchday', 'home_team', 'away_team', 'kickoff', 'result', 'is_processed']
    list_filter = ['matchday', 'result', 'is_processed']
    search_fields = ['home_team__name', 'away_team__name']

@admin.register(GamePool)
class GamePoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'season', 'created_by', 'is_active', 'entry_fee']
    list_filter = ['season', 'is_active']

@admin.register(PlayerEntry)
class PlayerEntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'game_pool', 'is_eliminated', 'eliminated_matchday']
    list_filter = ['game_pool', 'is_eliminated']
    search_fields = ['user__username']

@admin.register(Pick)
class PickAdmin(admin.ModelAdmin):
    list_display = ['player_entry', 'matchday', 'team', 'created_at', 'is_successful']
    list_filter = ['matchday', 'is_successful']
    search_fields = ['player_entry__user__username', 'team__name']