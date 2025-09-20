#!/usr/bin/env python3
import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_button():
    User = get_user_model()
    admin_user = User.objects.filter(is_superuser=True).first()
    
    client = Client()
    client.login(username=admin_user.username, password='admin')
    
    # Test admin page
    response = client.get('/admin/updates/versioncheck/')
    print(f"Admin page status: {response.status_code}")
    
    content = response.content.decode('utf-8')
    if '🔍 Check for Updates Now' in content:
        print("✅ Check button found in HTML!")
    else:
        print("❌ Check button NOT found")
    
    if 'check_updates=1' in content:
        print("✅ Check URL found!")
    else:
        print("❌ Check URL NOT found")
    
    if 'Current Installed Version' in content:
        print("✅ Current version display found!")
    else:
        print("❌ Current version display NOT found")
        
    if '📦' in content:
        print("✅ Version icon found!")
    else:
        print("❌ Version icon NOT found")
    
    # Check for install update button
    if 'Install Update' in content:
        print("✅ Install Update button found!")
    else:
        print("❌ Install Update button NOT found")
    
    # Test clicking the check updates button
    response = client.get('/admin/updates/versioncheck/?check_updates=1')
    print(f"Check updates response: {response.status_code}")
    
    # Check if we have messages
    from django.contrib.messages import get_messages
    if hasattr(response, 'wsgi_request'):
        messages = list(get_messages(response.wsgi_request))
        for message in messages:
            print(f"Message: {message}")
    
    # Now check if install button appears after update check
    response = client.get('/admin/updates/versioncheck/')
    content = response.content.decode('utf-8')
    if 'Install Update' in content:
        print("✅ Install Update button appeared after check!")
        
        # Test install button (but don't actually install)
        print("🧪 Testing install update URL (simulation mode)")
        if 'install_update=1' in content:
            print("✅ Install URL parameter found!")
        else:
            print("❌ Install URL parameter NOT found")
    else:
        print("❌ Install Update button NOT found after check")

if __name__ == '__main__':
    test_button()