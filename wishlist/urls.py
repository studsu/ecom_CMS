from django.urls import path
from . import views

app_name = 'wishlist'

urlpatterns = [
    path('', views.wishlist_view, name='wishlist'),
    path('add/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('clear/', views.clear_wishlist, name='clear_wishlist'),
    path('count/', views.wishlist_count, name='wishlist_count'),
    path('share/', views.share_wishlist, name='share_wishlist'),
]