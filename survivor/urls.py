from django.urls import path
from . import views

app_name = 'survivor'
urlpatterns = [
    path('pool/<int:pool_id>/', views.pool_detail, name='pool_detail'),
    path('pool/<int:pool_id>/pick/', views.make_pick, name='make_pick'),
    path('pool/<int:pool_id>/join/', views.join_pool, name='join_pool'),
    path('pool/create/', views.create_pool, name='create_pool'),
    path('int:matchday_id>/', views.matchday_results, name='matchday_results')
]