from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile, UserAddress

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    pass

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'date_of_birth', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email', 'phone']

@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'type', 'city', 'state', 'is_default', 'created_at']
    list_filter = ['type', 'is_default', 'country', 'state', 'created_at']
    search_fields = ['user__username', 'name', 'city', 'state', 'postal_code']
    list_editable = ['is_default']
