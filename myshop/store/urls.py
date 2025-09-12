from django.urls import path
from . import views
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .google_merchant import google_merchant_feed_view

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),  # ✅ This is required
    
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('bulk-order/<slug:slug>/', views.bulk_order_view, name='bulk_order'),

    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
   
    path('checkout/', views.checkout, name='checkout'),
    path('order-success/', views.order_success, name='order_success'),
    path('accounts/orders/<int:order_id>/', views.order_detail_view, name='order_detail'),

    path('accounts/', include('accounts.urls')),  # ✅ Add this line
    path('payment/', include('payments.urls')),


    path('cart/', views.view_cart, name='view_cart'),
    path('update-cart/', views.update_cart, name='update_cart'),
    path('save-for-later/<int:item_id>/', views.save_for_later, name='save_for_later'),
    path('move-to-cart/<int:item_id>/', views.move_to_cart, name='move_to_cart'),
    path('remove-cart-item/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('clear-cart/', views.clear_cart, name='clear_cart'),


    path('contact/', views.contact_view, name='contact_us'),


    #policies
    path("policy/payment/", views.payment_policy, name="payment_policy"),
    path("policy/shipping/", views.shipping_policy, name="shipping_policy"),
    path("policy/return/", views.return_policy, name="return_policy"),
    path("policy/terms/", views.terms_and_conditions, name="terms_and_conditions"),
    path("policy/privacy/", views.privacy_policy, name="privacy_policy"),

    # Google Merchant Center Feed
    path('google-merchant-feed.xml', google_merchant_feed_view, name='google_merchant_feed'),

    # Review URLs
    path('products/<slug:slug>/add-review/', views.add_review, name='add_review'),
    path('products/<slug:slug>/edit-review/<int:review_id>/', views.edit_review, name='edit_review'),
    path('products/<slug:slug>/delete-review/<int:review_id>/', views.delete_review, name='delete_review'),
    path('reviews/<int:review_id>/toggle-helpful/', views.toggle_review_helpful, name='toggle_review_helpful'),

]

