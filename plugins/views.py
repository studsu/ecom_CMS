from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from catalog.models import Product
from .forms import ReviewForm
from .models import Review

@login_required
def add_review(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug, is_active=True)
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            obj, created = Review.objects.get_or_create(
                product=product, user=request.user,
                defaults=form.cleaned_data
            )
            if not created:
                # update existing review if user already has one
                for f, v in form.cleaned_data.items():
                    setattr(obj, f, v)
                obj.save()
            messages.success(request, "Thank you! Your review has been saved.")
        else:
            messages.error(request, "Please fix the errors and try again.")
    return redirect(reverse("catalog:product_detail", kwargs={"slug": product.slug}))
