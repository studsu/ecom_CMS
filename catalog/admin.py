from django.contrib import admin
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "price", "is_active", "created_at")
    list_filter = ("is_active", "category")
    search_fields = ["title", "description"]
    prepopulated_fields = {"slug": ("title",)}
