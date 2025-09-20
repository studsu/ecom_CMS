from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import VersionCheck, UpdateSettings
from .git_checker import git_checker
import json


@staff_member_required
@require_POST
def check_updates_ajax(request):
    """AJAX endpoint for checking updates"""
    try:
        # Get settings
        settings = UpdateSettings.get_settings()
        
        # Check for updates
        result = git_checker.check_for_updates(
            include_prereleases=settings.include_prereleases
        )
        
        # Log the check
        check_log = VersionCheck.objects.create(
            current_version=result['current_version'],
            latest_version=result.get('latest_version', ''),
            update_available=result.get('update_available', False),
            check_successful=result['success'],
            error_message=result.get('error', ''),
        )
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'current_version': git_checker.get_current_version(),
            'latest_version': git_checker.get_current_version(),
            'update_available': False,
        })
