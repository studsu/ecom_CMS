"""
Git-based version checker for the CMS
Checks Git tags from remote repository to determine if updates are available
"""
import subprocess
import requests
import json
import re
import platform
from packaging import version
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class GitVersionChecker:
    """Check for updates from Git tags"""

    def __init__(self):
        self.repo_owner = "studsu"
        self.repo_name = "ecom_CMS"
        self.api_base = "https://api.github.com"
        self.cache_timeout = 300  # 5 minutes
        self._ssl_configured = False

    def _configure_git_ssl(self):
        """Configure Git SSL settings for Windows"""
        try:
            if platform.system() == 'Windows':
                # Disable SSL certificate revocation checking for Windows
                subprocess.run(['git', 'config', '--global', 'http.schannelCheckRevoke', 'false'],
                             capture_output=True, cwd=settings.BASE_DIR)
                subprocess.run(['git', 'config', '--global', 'http.sslVerify', 'true'],
                             capture_output=True, cwd=settings.BASE_DIR)
                logger.info("Configured Git SSL settings for Windows")
                self._ssl_configured = True
            return True
        except Exception as e:
            logger.error(f"Failed to configure Git SSL settings: {e}")
            return False

    def _run_git_command(self, cmd, retry_on_ssl_error=True):
        """Run git command with SSL error handling"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=settings.BASE_DIR)

            # Check for SSL/TLS errors (common on Windows)
            ssl_error_keywords = [
                'schannel', 'ssl', 'tls', 'certificate', 'handshake',
                'server closed abruptly', 'missing close_notify'
            ]

            if (result.returncode != 0 and retry_on_ssl_error and
                any(keyword in result.stderr.lower() for keyword in ssl_error_keywords)):

                logger.warning(f"SSL error detected in git command: {result.stderr}")

                # Configure SSL settings and retry
                if self._configure_git_ssl():
                    logger.info("Retrying git command after SSL configuration")
                    result = subprocess.run(cmd, capture_output=True, text=True, cwd=settings.BASE_DIR)

                    if result.returncode == 0:
                        logger.info("Git command succeeded after SSL configuration")

            return result

        except Exception as e:
            logger.error(f"Error running git command {cmd}: {e}")
            # Return a failed result object
            class FailedResult:
                def __init__(self, error):
                    self.returncode = 1
                    self.stdout = ""
                    self.stderr = str(error)
            return FailedResult(e)
    
    def get_current_version(self):
        """Get current version from Git tag or version file"""
        try:
            # Try to get version from git tag first
            result = self._run_git_command(
                ['git', 'describe', '--tags', '--exact-match', 'HEAD']
            )

            if result.returncode == 0:
                # Clean the tag (remove 'v' prefix if present)
                tag = result.stdout.strip()
                return tag.lstrip('v')

            # If no exact tag, get latest tag
            result = self._run_git_command(
                ['git', 'describe', '--tags', '--abbrev=0']
            )

            if result.returncode == 0:
                tag = result.stdout.strip()
                return tag.lstrip('v')
            
            # Fallback to version file or default
            version_file = settings.BASE_DIR / 'version.json'
            if version_file.exists():
                try:
                    with open(version_file, 'r') as f:
                        data = json.load(f)
                        return data.get('version', '1.0.0')
                except:
                    pass
            
            return '1.0.0'  # Default version
            
        except Exception as e:
            logger.error(f"Error getting current version: {e}")
            return '1.0.0'
    
    def get_remote_tags(self, include_prereleases=False):
        """Get version tags from remote Git repository"""
        try:
            cache_key = f"remote_tags_{include_prereleases}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data

            # Fetch latest tags from remote
            result = self._run_git_command(['git', 'fetch', '--tags'])
            if result.returncode != 0:
                logger.error(f"Failed to fetch tags: {result.stderr}")
                return []

            # Get all tags sorted by version
            result = self._run_git_command(['git', 'tag', '-l', '--sort=-version:refname'])
            if result.returncode != 0:
                logger.error(f"Failed to list tags: {result.stderr}")
                return []

            tags = []
            for tag_line in result.stdout.strip().split('\n'):
                tag = tag_line.strip()
                if not tag:
                    continue

                # Filter version tags (should start with 'v' or be numeric)
                if tag.startswith('v') or tag.replace('.', '').isdigit():
                    # Skip prerelease tags if not requested
                    if not include_prereleases and ('alpha' in tag.lower() or 'beta' in tag.lower() or 'rc' in tag.lower()):
                        continue

                    # Get commit info for this tag
                    commit_result = self._run_git_command(['git', 'show', '-s', '--format=%H|%ci|%s', tag])
                    commit_info = commit_result.stdout.strip().split('|') if commit_result.returncode == 0 else ['', '', '']

                    tags.append({
                        'tag_name': tag,
                        'name': f'Release {tag}',
                        'commit_hash': commit_info[0] if len(commit_info) > 0 else '',
                        'published_at': commit_info[1] if len(commit_info) > 1 else '',
                        'body': commit_info[2] if len(commit_info) > 2 else f'Release {tag}',
                        'prerelease': 'alpha' in tag.lower() or 'beta' in tag.lower() or 'rc' in tag.lower(),
                        'html_url': f"https://github.com/{self.repo_owner}/{self.repo_name}/releases/tag/{tag}"
                    })

            # Cache the result
            cache.set(cache_key, tags, self.cache_timeout)
            return tags

        except Exception as e:
            logger.error(f"Error fetching remote tags: {e}")
            return []
    
    def get_latest_version(self, include_prereleases=False):
        """Get the latest version from remote Git tags"""
        tags = self.get_remote_tags(include_prereleases)

        if not tags:
            return None

        # Tags are already sorted by version (newest first)
        # Find the latest version
        for tag_info in tags:
            tag_name = tag_info.get('tag_name', '')
            if tag_name:
                # Clean the tag (remove 'v' prefix if present)
                clean_version = tag_name.lstrip('v')
                return {
                    'version': clean_version,
                    'tag_name': tag_name,
                    'name': tag_info.get('name', ''),
                    'body': tag_info.get('body', ''),
                    'prerelease': tag_info.get('prerelease', False),
                    'published_at': tag_info.get('published_at'),
                    'html_url': tag_info.get('html_url', ''),
                }

        return None
    
    def check_for_updates(self, include_prereleases=False):
        """Check if updates are available"""
        try:
            current_version = self.get_current_version()
            latest_release = self.get_latest_version(include_prereleases)
            
            if not latest_release:
                return {
                    'success': False,
                    'error': 'Unable to fetch version information from remote repository',
                    'current_version': current_version,
                    'latest_version': current_version,
                    'update_available': False,
                }
            
            latest_version = latest_release['version']
            
            # Compare versions
            try:
                update_available = version.parse(latest_version) > version.parse(current_version)
            except Exception as e:
                # Fallback to string comparison if version parsing fails
                logger.warning(f"Version parsing failed, using string comparison: {e}")
                update_available = latest_version != current_version
            
            return {
                'success': True,
                'current_version': current_version,
                'latest_version': latest_version,
                'update_available': update_available,
                'release_name': latest_release['name'],
                'release_notes': latest_release['body'][:500] + '...' if len(latest_release['body']) > 500 else latest_release['body'],
                'prerelease': latest_release['prerelease'],
                'published_at': latest_release['published_at'],
                'release_url': latest_release['html_url'],
            }
            
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return {
                'success': False,
                'error': str(e),
                'current_version': self.get_current_version(),
                'latest_version': self.get_current_version(),
                'update_available': False,
            }
    
    def install_update(self, target_version):
        """Install update by pulling and checking out the specified version"""
        try:
            current_version = self.get_current_version()
            
            # Ensure we have a clean working directory
            result = self._run_git_command(['git', 'status', '--porcelain'])

            if result.stdout.strip():
                return {
                    'success': False,
                    'error': 'Working directory is not clean. Please commit or stash changes before updating.',
                    'current_version': current_version,
                }

            # Fetch latest changes from remote
            result = self._run_git_command(['git', 'fetch', '--tags'])

            if result.returncode != 0:
                return {
                    'success': False,
                    'error': f'Failed to fetch updates: {result.stderr}',
                    'current_version': current_version,
                }

            # Checkout the target version
            tag_name = target_version if target_version.startswith('v') else f'v{target_version}'
            result = self._run_git_command(['git', 'checkout', tag_name])

            if result.returncode != 0:
                # Try without 'v' prefix
                result = self._run_git_command(['git', 'checkout', target_version])

                if result.returncode != 0:
                    return {
                        'success': False,
                        'error': f'Failed to checkout version {target_version}: {result.stderr}',
                        'current_version': current_version,
                    }
            
            # Update version file if it exists
            version_file = settings.BASE_DIR / 'version.json'
            if version_file.exists():
                try:
                    with open(version_file, 'w') as f:
                        json.dump({'version': target_version}, f, indent=2)
                except Exception as e:
                    logger.warning(f"Could not update version file: {e}")
            
            new_version = self.get_current_version()
            
            return {
                'success': True,
                'message': f'Successfully updated from {current_version} to {new_version}',
                'old_version': current_version,
                'new_version': new_version,
            }
            
        except Exception as e:
            logger.error(f"Error installing update: {e}")
            return {
                'success': False,
                'error': str(e),
                'current_version': self.get_current_version(),
            }


# Global instance
git_checker = GitVersionChecker()