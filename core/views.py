# core/views.py
from django.shortcuts import render
from catalog.models import Product, Category

def home(request):
    # Get featured products and categories for homepage
    featured_products = Product.objects.filter(is_active=True)[:8]
    categories = Category.objects.all()[:6]

    context = {
        'featured_products': featured_products,
        'categories': categories,
    }
    return render(request, "home.html", context)
