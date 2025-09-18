from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.exceptions import PermissionDenied
from django.utils import timezone
import json
import asyncio
import threading

from .models import UpdateSettings, UpdateCheck, UpdateLog, AvailableUpdate, UpdateNotification
from core.version import cms_version


@staff_member_required
def update_dashboard(request):
    """Main update dashboard for admins"""

    settings = UpdateSettings.get_settings()
    current_version = cms_version.get_current_version()

    # Get recent update checks
    recent_checks = UpdateCheck.objects.all()[:5]

    # Get available updates
    available_updates = AvailableUpdate.objects.filter(installed=False)

    # Get recent update logs
    recent_updates = UpdateLog.objects.all()[:5]

    # Get unread notifications
    notifications = UpdateNotification.objects.filter(read=False)[:10]

    # Get version history
    version_history = cms_version.get_version_history()[:5]

    context = {
        'settings': settings,
        'current_version': current_version,
        'recent_checks': recent_checks,
        'available_updates': available_updates,
        'recent_updates': recent_updates,
        'notifications': notifications,
        'version_history': version_history,
    }

    return render(request, 'updates/dashboard.html', context)


@staff_member_required
@require_POST
def check_updates(request):
    """Check for updates via AJAX"""
    try:
        current_version = cms_version.get_current_version()

        # Check for updates
        update_info = cms_version.check_for_updates()

        # Log the check
        check_log = UpdateCheck.objects.create(
            current_version=current_version,
            latest_version=update_info.get('latest_version', ''),
            update_available=update_info.get('update_available', False),
            critical_update=update_info.get('critical', False),
            check_successful='error' not in update_info,
            error_message=update_info.get('error', ''),
            response_data=update_info
        )

        # If update available, save it
        if update_info.get('update_available'):
            AvailableUpdate.objects.get_or_create(
                version=update_info['latest_version'],
                defaults={
                    'release_date': timezone.now(),
                    'download_url': update_info.get('download_url', ''),
                    'file_size': update_info.get('file_size', 0),
                    'checksum': update_info.get('checksum', ''),
                    'critical': update_info.get('critical', False),
                    'release_notes': update_info.get('release_notes', ''),
                }
            )

            # Create notification
            UpdateNotification.objects.create(
                notification_type='critical_update' if update_info.get('critical') else 'update_available',
                title=f"Version {update_info['latest_version']} Available",
                message=f"A new {'critical ' if update_info.get('critical') else ''}update is available.",
                related_version=update_info['latest_version']
            )

        return JsonResponse({
            'success': True,
            'update_available': update_info.get('update_available', False),
            'latest_version': update_info.get('latest_version', ''),
            'critical': update_info.get('critical', False),
            'message': 'Update check completed successfully'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@staff_member_required
@require_POST
def install_update(request):
    """Install available update"""
    try:
        data = json.loads(request.body)
        version = data.get('version')

        if not version:
            return JsonResponse({'success': False, 'error': 'Version required'})

        # Get the available update
        try:
            available_update = AvailableUpdate.objects.get(version=version, installed=False)
        except AvailableUpdate.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Update not found'})

        # Create update log
        current_version = cms_version.get_current_version()
        update_log = UpdateLog.objects.create(
            from_version=current_version,
            to_version=version,
            initiated_by=request.user,
            release_notes=available_update.release_notes
        )

        return JsonResponse({
            'success': True,
            'message': 'Update started successfully',
            'update_log_id': update_log.id
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@staff_member_required
def update_status(request, update_log_id):
    """Get update status via AJAX"""
    try:
        update_log = UpdateLog.objects.get(id=update_log_id)

        return JsonResponse({
            'success': True,
            'status': update_log.status,
            'completed': update_log.status in ['completed', 'failed', 'rolled_back'],
            'error_message': update_log.error_message,
            'duration': str(update_log.duration) if update_log.duration else None
        })

    except UpdateLog.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Update log not found'
        })


@staff_member_required
@require_POST
def rollback_update(request):
    """Rollback to previous version"""
    try:
        data = json.loads(request.body)
        backup_path = data.get('backup_path')

        if not backup_path:
            return JsonResponse({'success': False, 'error': 'Backup path required'})

        # Perform rollback
        success = cms_version.rollback(backup_path)

        if success:
            return JsonResponse({
                'success': True,
                'message': 'Rollback completed successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Rollback failed'
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@staff_member_required
def update_settings_view(request):
    """Update settings page"""
    settings = UpdateSettings.get_settings()

    if request.method == 'POST':
        # Update settings
        settings.auto_check_enabled = request.POST.get('auto_check_enabled') == 'on'
        settings.auto_install_enabled = request.POST.get('auto_install_enabled') == 'on'
        settings.check_frequency = request.POST.get('check_frequency', 'weekly')
        settings.install_critical_updates = request.POST.get('install_critical_updates') == 'on'
        settings.backup_before_update = request.POST.get('backup_before_update') == 'on'
        settings.max_backups_to_keep = int(request.POST.get('max_backups_to_keep', 5))
        settings.update_server_url = request.POST.get('update_server_url', '')
        settings.api_key = request.POST.get('api_key', '')
        settings.notification_email = request.POST.get('notification_email', '')
        settings.beta_updates = request.POST.get('beta_updates') == 'on'

        settings.save()
        messages.success(request, 'Update settings saved successfully')
        return redirect('updates:settings')

    return render(request, 'updates/settings.html', {'settings': settings})


@staff_member_required
def notifications_view(request):
    """View and manage update notifications"""
    notifications = UpdateNotification.objects.all()[:50]

    if request.method == 'POST':
        action = request.POST.get('action')
        notification_id = request.POST.get('notification_id')

        if action == 'mark_read' and notification_id:
            try:
                notification = UpdateNotification.objects.get(id=notification_id)
                notification.mark_read()
                messages.success(request, 'Notification marked as read')
            except UpdateNotification.DoesNotExist:
                messages.error(request, 'Notification not found')

        elif action == 'mark_all_read':
            UpdateNotification.objects.filter(read=False).update(
                read=True,
                read_at=timezone.now()
            )
            messages.success(request, 'All notifications marked as read')

    return render(request, 'updates/notifications.html', {'notifications': notifications})


@staff_member_required
def version_history_view(request):
    """View version history and backups"""
    version_history = cms_version.get_version_history()
    current_version = cms_version.get_current_version()

    return render(request, 'updates/version_history.html', {
        'version_history': version_history,
        'current_version': current_version
    })
