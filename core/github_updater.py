"""
GitHub-based Auto-Update System for Ecom CMS
Automatically checks GitHub releases and notifies all CMS installations
"""

import requests
import json
import re
from datetime import datetime, timezone
from packaging import version
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class GitHubUpdater:
    """Handles GitHub releases-based updates"""
    
    def __init__(self):
        # GitHub repository details - UPDATE THESE TO YOUR REPO
        self.github_owner = "studsu"  # Your GitHub username
        self.github_repo = "ecom_CMS"  # Your repository name
        self.api_base = "https://api.github.com"
        self.releases_url = f"{self.api_base}/repos/{self.github_owner}/{self.github_repo}/releases"
        self.cache_timeout = 300  # 5 minutes cache
        
    def get_latest_release(self, include_prereleases=False):
        """Get latest release from GitHub"""
        try:
            cache_key = f"github_latest_release_{include_prereleases}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data
                
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Ecom-CMS-Updater/1.0'
            }
            
            # Add GitHub token if available (for higher rate limits)
            github_token = getattr(settings, 'GITHUB_TOKEN', None)
            if github_token:
                headers['Authorization'] = f'token {github_token}'
            
            if include_prereleases:
                # Get all releases and filter
                response = requests.get(self.releases_url, headers=headers, timeout=10)
            else:
                # Get latest stable release
                response = requests.get(f"{self.releases_url}/latest", headers=headers, timeout=10)
            
            response.raise_for_status()
            release_data = response.json()
            
            # Cache the result
            cache.set(cache_key, release_data, self.cache_timeout)
            return release_data
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch GitHub release: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing GitHub release: {e}")
            return None
    
    def check_for_updates(self, current_version, include_prereleases=False):
        """Check if updates are available"""
        try:
            release = self.get_latest_release(include_prereleases)
            if not release:
                return {
                    'error': 'Unable to check for updates',
                    'update_available': False
                }
            
            latest_version = release['tag_name'].lstrip('v')  # Remove 'v' prefix if present
            
            # Compare versions
            current_ver = version.parse(current_version)
            latest_ver = version.parse(latest_version)
            
            update_available = latest_ver > current_ver
            
            # Find download URL (look for .zip asset)
            download_url = None
            file_size = 0
            
            for asset in release.get('assets', []):
                if asset['name'].endswith('.zip') and 'source' not in asset['name'].lower():
                    download_url = asset['browser_download_url']
                    file_size = asset['size']
                    break
            
            # If no custom asset, use source code zip
            if not download_url:
                download_url = release['zipball_url']
            
            return {
                'update_available': update_available,
                'latest_version': latest_version,
                'current_version': current_version,
                'release_name': release['name'],
                'release_notes': release['body'],
                'download_url': download_url,
                'file_size': file_size,
                'published_at': release['published_at'],
                'prerelease': release['prerelease'],
                'critical': self._is_critical_update(release),
                'github_url': release['html_url']
            }
            
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return {
                'error': str(e),
                'update_available': False
            }
    
    def _is_critical_update(self, release):
        """Determine if this is a critical update based on release notes"""
        critical_keywords = [
            'security', 'critical', 'urgent', 'hotfix', 
            'vulnerability', 'exploit', 'patch'
        ]
        
        release_text = (release.get('body', '') + release.get('name', '')).lower()
        return any(keyword in release_text for keyword in critical_keywords)
    
    def get_all_releases(self, limit=10):
        """Get recent releases for version history"""
        try:
            cache_key = f"github_all_releases_{limit}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data
                
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Ecom-CMS-Updater/1.0'
            }
            
            github_token = getattr(settings, 'GITHUB_TOKEN', None)
            if github_token:
                headers['Authorization'] = f'token {github_token}'
            
            params = {'per_page': limit}
            response = requests.get(self.releases_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            releases = response.json()
            
            # Process releases
            processed_releases = []
            for release in releases:
                processed_releases.append({
                    'version': release['tag_name'].lstrip('v'),
                    'name': release['name'],
                    'published_at': release['published_at'],
                    'prerelease': release['prerelease'],
                    'body': release['body'][:500] + '...' if len(release['body']) > 500 else release['body'],
                    'html_url': release['html_url']
                })
            
            cache.set(cache_key, processed_releases, self.cache_timeout)
            return processed_releases
            
        except Exception as e:
            logger.error(f"Error fetching releases: {e}")
            return []
    
    def download_release(self, download_url, destination_path):
        """Download release file"""
        try:
            headers = {
                'User-Agent': 'Ecom-CMS-Updater/1.0'
            }
            
            github_token = getattr(settings, 'GITHUB_TOKEN', None)
            if github_token:
                headers['Authorization'] = f'token {github_token}'
            
            response = requests.get(download_url, headers=headers, stream=True, timeout=300)
            response.raise_for_status()
            
            with open(destination_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return True
            
        except Exception as e:
            logger.error(f"Error downloading release: {e}")
            return False
    
    def validate_github_config(self):
        """Validate GitHub configuration"""
        try:
            # Test API access
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Ecom-CMS-Updater/1.0'
            }
            
            github_token = getattr(settings, 'GITHUB_TOKEN', None)
            if github_token:
                headers['Authorization'] = f'token {github_token}'
            
            repo_url = f"{self.api_base}/repos/{self.github_owner}/{self.github_repo}"
            response = requests.get(repo_url, headers=headers, timeout=10)
            
            if response.status_code == 404:
                return False, "Repository not found. Check owner/repo names."
            elif response.status_code == 403:
                return False, "Access denied. Repository may be private or rate limited."
            elif response.status_code == 200:
                return True, "GitHub configuration is valid."
            else:
                return False, f"Unexpected response: {response.status_code}"
                
        except Exception as e:
            return False, f"Configuration error: {str(e)}"

# Global instance
github_updater = GitHubUpdater()