from django.shortcuts import render, get_object_or_404
from .models import Product, Category

def product_list(request):
    qs = Product.objects.filter(is_active=True).select_related("category").order_by("-created_at")
    return render(request, "catalog/product_list.html", {"products": qs})

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, "catalog/product_detail.html", {"product": product})
