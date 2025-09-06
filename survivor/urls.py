from django.urls import path
from . import views
from . import admin_views

app_name = 'survivor'
urlpatterns = [
    path('pool/<int:pool_id>/', views.pool_detail, name='pool_detail'),
    path('pool/<int:pool_id>/pick/', views.make_pick, name='make_pick'),
    path('pool/<int:pool_id>/join/', views.join_pool, name='join_pool'),
    path('pool/<int:pool_id>/history/', views.pick_history, name='pick_history'),
    path('pool/<int:pool_id>/fixtures/', views.fixtures, name='pool_fixtures'),
    path('pool/create/', views.create_pool, name='create_pool'),
    path('fixtures/', views.fixtures, name='fixtures'),
    path('matchday/<int:matchday_id>/', views.matchday_fixtures, name='matchday_fixtures'),
    
    # Admin sync URLs
    path('admin/sync/', admin_views.sync_dashboard, name='sync_dashboard'),
    path('admin/sync/teams/', admin_views.sync_teams, name='sync_teams'),
    path('admin/sync/fixtures/', admin_views.sync_fixtures, name='sync_fixtures'),
    path('admin/sync/results/', admin_views.process_results, name='process_results'),
    path('admin/sync/all/', admin_views.quick_sync_all, name='quick_sync_all'),
]