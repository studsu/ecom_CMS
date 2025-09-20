"""
Management command to check for GitHub updates
Usage: python manage.py check_github_updates
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from updates.models import UpdateSettings, UpdateCheck, AvailableUpdate, UpdateNotification
from core.version import cms_version
import json


class Command(BaseCommand):
    help = 'Check for updates from GitHub releases'

    def add_arguments(self, parser):
        parser.add_argument(
            '--auto-install',
            action='store_true',
            help='Automatically install critical updates'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force check ignoring settings'
        )
        parser.add_argument(
            '--notify',
            action='store_true',
            help='Send email notification if updates found'
        )

    def handle(self, *args, **options):
        self.stdout.write("🔍 Checking for GitHub updates...")
        
        try:
            settings = UpdateSettings.get_settings()
            
            # Check if auto-check is enabled (unless forced)
            if not options['force'] and not settings.auto_check_enabled:
                self.stdout.write(
                    self.style.WARNING("Auto-check is disabled. Use --force to override.")
                )
                return

            # Get current version
            current_version = cms_version.get_current_version()
            self.stdout.write(f"Current version: {current_version}")

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

            if update_info.get('error'):
                self.stdout.write(
                    self.style.ERROR(f"❌ Error: {update_info['error']}")
                )
                return

            if update_info.get('update_available'):
                latest_version = update_info['latest_version']
                is_critical = update_info.get('critical', False)
                
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Update available: {latest_version}")
                )
                
                if is_critical:
                    self.stdout.write(
                        self.style.WARNING("🚨 This is a CRITICAL update!")
                    )

                # Save available update
                available_update, created = AvailableUpdate.objects.get_or_create(
                    version=latest_version,
                    defaults={
                        'release_date': timezone.now(),
                        'download_url': update_info.get('download_url', ''),
                        'file_size': update_info.get('file_size', 0),
                        'checksum': update_info.get('checksum', ''),
                        'critical': is_critical,
                        'release_notes': update_info.get('release_notes', ''),
                    }
                )

                # Create notification
                notification_type = 'critical_update' if is_critical else 'update_available'
                UpdateNotification.objects.create(
                    notification_type=notification_type,
                    title=f"Version {latest_version} Available",
                    message=f"A new {'critical ' if is_critical else ''}update is available from GitHub.",
                    related_version=latest_version,
                    action_url='/admin/updates/availableupdate/',
                    action_label='View Updates'
                )

                # Auto-install if enabled and critical
                if (options['auto_install'] or 
                    (is_critical and settings.install_critical_updates)):
                    
                    self.stdout.write("🔄 Auto-installing update...")
                    # Here you would trigger the update installation
                    # For safety, we'll just show the message
                    self.stdout.write(
                        self.style.WARNING(
                            "Auto-install would be triggered here. "
                            "Implement update installation logic in updates/views.py"
                        )
                    )

                # Send email notification if requested
                if options['notify'] and settings.notification_email:
                    self.stdout.write("📧 Sending email notification...")
                    # Add email notification logic here
                    
                self.stdout.write(
                    self.style.SUCCESS(
                        f"📦 Release Notes:\n{update_info.get('release_notes', 'No release notes available')[:200]}..."
                    )
                )

            else:
                self.stdout.write(
                    self.style.SUCCESS("✅ No updates available. You're running the latest version!")
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error checking for updates: {str(e)}")
            )
            
            # Log failed check
            UpdateCheck.objects.create(
                current_version=cms_version.get_current_version(),
                check_successful=False,
                error_message=str(e)
            )