"""
Management command to check for CMS updates
Can be run manually or via cron job for automatic checking
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from updates.models import UpdateSettings, UpdateCheck, AvailableUpdate, UpdateNotification
from core.version import cms_version
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check for CMS updates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force check even if auto-check is disabled',
        )
        parser.add_argument(
            '--auto-install',
            action='store_true',
            help='Automatically install non-critical updates',
        )
        parser.add_argument(
            '--notify',
            action='store_true',
            help='Send email notification if updates available',
        )

    def handle(self, *args, **options):
        update_settings = UpdateSettings.get_settings()

        # Check if auto-check is enabled (unless forced)
        if not update_settings.auto_check_enabled and not options['force']:
            self.stdout.write(self.style.WARNING('Auto-check is disabled. Use --force to check anyway.'))
            return

        self.stdout.write('Checking for updates...')

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

            if 'error' in update_info:
                self.stdout.write(self.style.ERROR(f"Error checking updates: {update_info['error']}"))
                return

            if not update_info.get('update_available'):
                self.stdout.write(self.style.SUCCESS('No updates available. CMS is up to date.'))
                return

            # Update is available
            latest_version = update_info['latest_version']
            is_critical = update_info.get('critical', False)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Update available: {current_version} → {latest_version} "
                    f"({'CRITICAL' if is_critical else 'Normal'})"
                )
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

            if created:
                self.stdout.write(f"Saved new available update: {latest_version}")

            # Create notification
            notification_type = 'critical_update' if is_critical else 'update_available'
            UpdateNotification.objects.create(
                notification_type=notification_type,
                title=f"Version {latest_version} Available",
                message=f"A new {'critical ' if is_critical else ''}update is available.",
                related_version=latest_version
            )

            # Auto-install if enabled and appropriate
            if self._should_auto_install(update_settings, is_critical, options):
                self.stdout.write('Starting automatic installation...')
                success = self._auto_install_update(available_update, update_settings)

                if success:
                    self.stdout.write(self.style.SUCCESS('Update installed successfully!'))
                else:
                    self.stdout.write(self.style.ERROR('Auto-installation failed. Manual installation required.'))

            # Send email notification if requested
            if options['notify'] or update_settings.notification_email:
                self._send_email_notification(update_settings, update_info, current_version)

        except Exception as e:
            logger.error(f"Error in update check command: {e}")
            self.stdout.write(self.style.ERROR(f"Error checking for updates: {e}"))

    def _should_auto_install(self, settings, is_critical, options):
        """Determine if update should be auto-installed"""
        if options['auto_install']:
            return True

        if is_critical and settings.install_critical_updates:
            return True

        if not is_critical and settings.auto_install_enabled:
            return True

        return False

    def _auto_install_update(self, available_update, settings):
        """Automatically install the update"""
        try:
            from updates.models import UpdateLog

            current_version = cms_version.get_current_version()

            # Create update log
            update_log = UpdateLog.objects.create(
                from_version=current_version,
                to_version=available_update.version,
                auto_update=True,
                release_notes=available_update.release_notes
            )

            self.stdout.write('Downloading update...')
            update_log.status = 'downloading'
            update_log.save()

            # Download update
            update_file = cms_version.download_update(
                available_update.download_url,
                available_update.checksum
            )

            # Create backup if enabled
            backup_path = None
            if settings.backup_before_update:
                self.stdout.write('Creating backup...')
                update_log.status = 'backing_up'
                update_log.save()

                backup_path = cms_version.create_backup()
                update_log.backup_path = backup_path
                update_log.save()

            # Install update
            self.stdout.write('Installing update...')
            update_log.status = 'installing'
            update_log.save()

            cms_version.apply_update(update_file, backup_path)

            # Mark as completed
            update_log.mark_completed()
            available_update.installed = True
            available_update.install_date = timezone.now()
            available_update.save()

            # Create success notification
            UpdateNotification.objects.create(
                notification_type='update_completed',
                title=f"Auto-Update to {available_update.version} Completed",
                message=f"Successfully updated from {current_version} to {available_update.version}",
                related_version=available_update.version
            )

            return True

        except Exception as e:
            logger.error(f"Auto-installation failed: {e}")
            update_log.mark_failed(str(e))

            # Create failure notification
            UpdateNotification.objects.create(
                notification_type='update_failed',
                title=f"Auto-Update to {available_update.version} Failed",
                message=f"Failed to auto-update: {str(e)}",
                related_version=available_update.version
            )

            return False

    def _send_email_notification(self, settings, update_info, current_version):
        """Send email notification about available update"""
        try:
            if not settings.notification_email:
                return

            subject = f"CMS Update Available: {update_info['latest_version']}"

            message = f"""
A new update is available for your CMS installation.

Current Version: {current_version}
Latest Version: {update_info['latest_version']}
Type: {'Critical Security Update' if update_info.get('critical') else 'Regular Update'}

Release Notes:
{update_info.get('release_notes', 'No release notes available.')}

Please log in to your admin panel to install the update.

Admin URL: {getattr(settings, 'SITE_URL', 'your-site.com')}/admin/

This is an automated message from your CMS update system.
            """

            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@yoursite.com'),
                recipient_list=[settings.notification_email],
                fail_silently=False,
            )

            self.stdout.write(f"Email notification sent to {settings.notification_email}")

        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            self.stdout.write(self.style.WARNING(f"Failed to send email notification: {e}"))