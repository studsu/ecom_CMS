from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "is_public", "created_at")
    list_filter = ("is_public", "rating", "created_at")
    search_fields = ("product__title", "user__username", "title", "comment")
    autocomplete_fields = ("product", "user")
