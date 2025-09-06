# survivor/admin_views.py
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.management import call_command
from django.http import JsonResponse
import logging
from io import StringIO

logger = logging.getLogger(__name__)

@staff_member_required
def sync_dashboard(request):
    """Admin dashboard for syncing data from football API"""
    context = {
        'title': 'Bundesliga Data Sync Dashboard'
    }
    return render(request, 'admin/sync_dashboard.html', context)

@staff_member_required
def sync_teams(request):
    """Sync teams from football API"""
    if request.method == 'POST':
        try:
            # Capture command output
            out = StringIO()
            call_command('sync_teams', stdout=out)
            output = out.getvalue()
            
            messages.success(request, 'Teams synced successfully!')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Teams synced successfully!',
                    'output': output
                })
        except Exception as e:
            logger.error(f"Error syncing teams: {e}")
            messages.error(request, f'Error syncing teams: {str(e)}')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)
    
    return redirect('survivor:sync_dashboard')

@staff_member_required
def sync_fixtures(request):
    """Sync fixtures from football API"""
    if request.method == 'POST':
        try:
            # Get optional parameters
            season = request.POST.get('season')
            matchday = request.POST.get('matchday')
            results_only = request.POST.get('results_only') == 'true'
            
            # Build command arguments
            kwargs = {}
            if season:
                kwargs['season'] = season
            if matchday:
                kwargs['matchday'] = int(matchday)
            if results_only:
                kwargs['results_only'] = True
            
            # Capture command output
            out = StringIO()
            call_command('sync_fixtures', stdout=out, **kwargs)
            output = out.getvalue()
            
            messages.success(request, 'Fixtures synced successfully!')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Fixtures synced successfully!',
                    'output': output
                })
        except Exception as e:
            logger.error(f"Error syncing fixtures: {e}")
            messages.error(request, f'Error syncing fixtures: {str(e)}')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)
    
    return redirect('survivor:sync_dashboard')

@staff_member_required
def process_results(request):
    """Process match results and eliminate players"""
    if request.method == 'POST':
        try:
            matchday = request.POST.get('matchday')
            
            kwargs = {}
            if matchday:
                kwargs['matchday'] = int(matchday)
            
            # Capture command output
            out = StringIO()
            call_command('process_results', stdout=out, **kwargs)
            output = out.getvalue()
            
            messages.success(request, 'Results processed successfully!')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Results processed successfully!',
                    'output': output
                })
        except Exception as e:
            logger.error(f"Error processing results: {e}")
            messages.error(request, f'Error processing results: {str(e)}')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)
    
    return redirect('survivor:sync_dashboard')

@staff_member_required
def quick_sync_all(request):
    """Quick sync everything - teams, current season fixtures, and process results"""
    if request.method == 'POST':
        try:
            output = []
            
            # 1. Sync teams
            out = StringIO()
            call_command('sync_teams', stdout=out)
            output.append(f"=== TEAMS SYNC ===\n{out.getvalue()}")
            
            # 2. Sync fixtures for current season (2024)
            out = StringIO()
            call_command('sync_fixtures', season=2024, stdout=out)
            output.append(f"\n=== FIXTURES SYNC ===\n{out.getvalue()}")
            
            # 3. Process results
            out = StringIO()
            call_command('process_results', stdout=out)
            output.append(f"\n=== PROCESS RESULTS ===\n{out.getvalue()}")
            
            full_output = '\n'.join(output)
            
            messages.success(request, 'All data synced successfully!')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': 'All data synced successfully!',
                    'output': full_output
                })
        except Exception as e:
            logger.error(f"Error in quick sync: {e}")
            messages.error(request, f'Error in quick sync: {str(e)}')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)
    
    return redirect('survivor:sync_dashboard')
