from django.urls import path
from . import views

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
]