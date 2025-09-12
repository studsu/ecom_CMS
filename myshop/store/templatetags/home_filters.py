from django import template
from store.models import Category

register = template.Library()

@register.filter
def get_category_by_slug(categories, slug):
    return categories.filter(slug=slug).first()

@register.filter
def slice_items(items, count):
    try:
        return items[:int(count)]
    except:
        return items

@register.filter
def active_products(category):
    """Get active products for a category"""
    if hasattr(category, 'product_set'):
        return category.product_set.filter(is_active=True)
    return category.filter(is_active=True) if hasattr(category, 'filter') else category
