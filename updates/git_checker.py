"""
Git-based version checker for the CMS
Checks GitHub releases to determine if updates are available
"""
import subprocess
import requests
import json
import re
from packaging import version
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class GitVersionChecker:
    """Check for updates from GitHub releases"""
    
    def __init__(self):
        self.repo_owner = "studsu"
        self.repo_name = "ecom_CMS"
        self.api_base = "https://api.github.com"
        self.cache_timeout = 300  # 5 minutes
    
    def get_current_version(self):
        """Get current version from Git tag or version file"""
        try:
            # Try to get version from git tag first
            result = subprocess.run(
                ['git', 'describe', '--tags', '--exact-match', 'HEAD'],
                capture_output=True,
                text=True,
                cwd=settings.BASE_DIR
            )
            
            if result.returncode == 0:
                # Clean the tag (remove 'v' prefix if present)
                tag = result.stdout.strip()
                return tag.lstrip('v')
            
            # If no exact tag, get latest tag
            result = subprocess.run(
                ['git', 'describe', '--tags', '--abbrev=0'],
                capture_output=True,
                text=True,
                cwd=settings.BASE_DIR
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
    
    def get_github_releases(self, include_prereleases=False):
        """Get releases from GitHub API"""
        try:
            cache_key = f"github_releases_{include_prereleases}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data
            
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': f'{self.repo_name}/1.0'
            }
            
            # Add GitHub token if available (for higher rate limits)
            github_token = getattr(settings, 'GITHUB_TOKEN', None)
            if github_token:
                headers['Authorization'] = f'token {github_token}'
            
            url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/releases"
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            releases = response.json()
            
            # Filter out prereleases if not requested
            if not include_prereleases:
                releases = [r for r in releases if not r.get('prerelease', False)]
            
            # Cache the result
            cache.set(cache_key, releases, self.cache_timeout)
            return releases
            
        except requests.RequestException as e:
            logger.error(f"Error fetching GitHub releases: {e}")
            return []
        except Exception as e:
            logger.error(f"Error processing GitHub releases: {e}")
            return []
    
    def get_latest_version(self, include_prereleases=False):
        """Get the latest version from GitHub releases"""
        releases = self.get_github_releases(include_prereleases)
        
        if not releases:
            return None
        
        # GitHub returns releases in reverse chronological order
        # Find the latest version
        for release in releases:
            tag_name = release.get('tag_name', '')
            if tag_name:
                # Clean the tag (remove 'v' prefix if present)
                clean_version = tag_name.lstrip('v')
                return {
                    'version': clean_version,
                    'tag_name': tag_name,
                    'name': release.get('name', ''),
                    'body': release.get('body', ''),
                    'prerelease': release.get('prerelease', False),
                    'published_at': release.get('published_at'),
                    'html_url': release.get('html_url', ''),
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
                    'error': 'Unable to fetch release information from GitHub',
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


# Global instance
git_checker = GitVersionChecker()