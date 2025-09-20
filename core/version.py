"""
Ecom CMS Version Management System
Handles version checking, updates, and release management
"""

import os
import json
import hashlib
import zipfile
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.core.management import execute_from_command_line
import logging

# Optional import for update functionality
try:
    import requests
    from packaging import version as version_parser
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)

class CMSVersion:
    """Central version management for Ecom CMS"""

    # Current version - update this with each release
    CURRENT_VERSION = "1.0.0"
    VERSION_FILE = "version.json"
    UPDATE_SERVER_URL = "https://api.yoursite.com/cms-updates"  # Your update server

    def __init__(self):
        self.base_dir = Path(settings.BASE_DIR)
        self.version_file_path = self.base_dir / self.VERSION_FILE
        self.backup_dir = self.base_dir / "backups"
        self.temp_dir = self.base_dir / "temp_updates"

    def get_current_version(self):
        """Get current installed version"""
        try:
            if self.version_file_path.exists():
                with open(self.version_file_path, 'r') as f:
                    version_data = json.load(f)
                    return version_data.get('version', self.CURRENT_VERSION)
            return self.CURRENT_VERSION
        except Exception as e:
            logger.error(f"Error reading version file: {e}")
            return self.CURRENT_VERSION

    def save_version_info(self, version, release_notes=None, install_date=None):
        """Save version information to file"""
        version_data = {
            'version': version,
            'install_date': install_date or datetime.now().isoformat(),
            'release_notes': release_notes,
            'last_check': datetime.now().isoformat()
        }

        try:
            with open(self.version_file_path, 'w') as f:
                json.dump(version_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving version info: {e}")
            return False

    def check_for_updates(self):
        """Check if updates are available from GitHub releases"""
        if not REQUESTS_AVAILABLE:
            return {'error': 'requests library not available. Run: pip install requests'}

        try:
            from .github_updater import github_updater
            
            current_version = self.get_current_version()
            
            # Get update settings to check for beta updates
            try:
                from updates.models import UpdateSettings
                settings_obj = UpdateSettings.get_settings()
                include_prereleases = settings_obj.beta_updates
            except:
                include_prereleases = False
            
            # Check GitHub for updates
            update_info = github_updater.check_for_updates(
                current_version=current_version,
                include_prereleases=include_prereleases
            )
            
            return update_info

        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return {'error': f'Error checking for updates: {str(e)}'}

    def download_update(self, download_url, checksum=None):
        """Download update package from GitHub"""
        if not REQUESTS_AVAILABLE:
            raise Exception('requests library not available. Run: pip install requests')

        try:
            from .github_updater import github_updater
            
            self.temp_dir.mkdir(exist_ok=True)
            update_file = self.temp_dir / "update.zip"

            logger.info(f"Downloading update from GitHub: {download_url}")

            # Use GitHub updater for download
            success = github_updater.download_release(download_url, str(update_file))
            
            if not success:
                raise Exception("Failed to download from GitHub")

            # Verify checksum if provided
            if checksum:
                if not self.verify_checksum(update_file, checksum):
                    raise Exception("Checksum verification failed")

            logger.info("Update downloaded successfully from GitHub")
            return str(update_file)

        except Exception as e:
            logger.error(f"Error downloading update: {e}")
            raise Exception(f"Failed to download update: {e}")

    def verify_checksum(self, file_path, expected_checksum):
        """Verify file checksum"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)

            actual_checksum = sha256_hash.hexdigest()
            return actual_checksum == expected_checksum
        except Exception as e:
            logger.error(f"Error verifying checksum: {e}")
            return False

    def create_backup(self):
        """Create backup before update"""
        try:
            self.backup_dir.mkdir(exist_ok=True)

            backup_name = f"backup_{self.get_current_version()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = self.backup_dir / f"{backup_name}.zip"

            logger.info(f"Creating backup: {backup_path}")

            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.base_dir):
                    # Skip backup, temp, and cache directories
                    dirs[:] = [d for d in dirs if d not in ['backups', 'temp_updates', '__pycache__', '.git']]

                    for file in files:
                        if file.endswith(('.pyc', '.pyo')):
                            continue

                        file_path = Path(root) / file
                        archive_path = file_path.relative_to(self.base_dir)
                        zipf.write(file_path, archive_path)

            logger.info("Backup created successfully")
            return str(backup_path)

        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise Exception(f"Failed to create backup: {e}")

    def apply_update(self, update_file_path, backup_path):
        """Apply the downloaded update"""
        try:
            logger.info("Applying update...")

            # Extract update
            extract_dir = self.temp_dir / "extracted"
            extract_dir.mkdir(exist_ok=True)

            with zipfile.ZipFile(update_file_path, 'r') as zipf:
                zipf.extractall(extract_dir)

            # Read update manifest
            manifest_path = extract_dir / "update_manifest.json"
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
            else:
                manifest = {}

            # Apply file updates
            self._apply_file_updates(extract_dir, manifest)

            # Run database migrations
            self._run_migrations()

            # Update version info
            new_version = manifest.get('version', 'unknown')
            self.save_version_info(
                version=new_version,
                release_notes=manifest.get('release_notes'),
                install_date=datetime.now().isoformat()
            )

            # Cleanup
            self._cleanup_temp_files()

            logger.info("Update applied successfully")
            return True

        except Exception as e:
            logger.error(f"Error applying update: {e}")
            # Attempt rollback
            self.rollback(backup_path)
            raise Exception(f"Update failed: {e}")

    def _apply_file_updates(self, extract_dir, manifest):
        """Apply file updates based on manifest"""
        update_files = manifest.get('files', [])

        for file_info in update_files:
            source_path = extract_dir / file_info['path']
            target_path = self.base_dir / file_info['path']

            if file_info['action'] == 'update':
                # Update/create file
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, target_path)

            elif file_info['action'] == 'delete':
                # Delete file
                if target_path.exists():
                    target_path.unlink()

    def _run_migrations(self):
        """Run Django database migrations"""
        try:
            logger.info("Running database migrations...")
            subprocess.run([
                'python', 'manage.py', 'migrate'
            ], cwd=self.base_dir, check=True, capture_output=True)
            logger.info("Migrations completed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Migration failed: {e}")
            raise Exception("Database migration failed")

    def _cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.warning(f"Error cleaning up temp files: {e}")

    def rollback(self, backup_path):
        """Rollback to previous version"""
        try:
            logger.info(f"Rolling back from backup: {backup_path}")

            # Extract backup
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(self.base_dir)

            logger.info("Rollback completed")
            return True

        except Exception as e:
            logger.error(f"Error during rollback: {e}")
            return False

    def get_version_history(self):
        """Get version history from backups"""
        try:
            if not self.backup_dir.exists():
                return []

            backups = []
            for backup_file in self.backup_dir.glob("backup_*.zip"):
                # Parse backup filename for version info
                parts = backup_file.stem.split('_')
                if len(parts) >= 3:
                    version = parts[1]
                    date_str = f"{parts[2]}_{parts[3]}"
                    try:
                        backup_date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                        backups.append({
                            'version': version,
                            'date': backup_date,
                            'file_path': str(backup_file),
                            'size': backup_file.stat().st_size
                        })
                    except ValueError:
                        continue

            return sorted(backups, key=lambda x: x['date'], reverse=True)

        except Exception as e:
            logger.error(f"Error getting version history: {e}")
            return []


# Singleton instance
cms_version = CMSVersion()