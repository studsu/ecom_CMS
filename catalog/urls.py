from django.urls import path
from .views import (
    product_list, product_detail, cart_add, cart_detail, 
    cart_remove, cart_update, add_review
)

urlpatterns = [
    path("", product_list, name="product_list"),
    path("cart/", cart_detail, name="cart_detail"),
    path("cart/add/<int:product_id>/", cart_add, name="cart_add"),
    path("cart/remove/<int:product_id>/", cart_remove, name="cart_remove"),
    path("cart/update/<int:product_id>/", cart_update, name="cart_update"),
    path("review/add/<int:product_id>/", add_review, name="add_review"),
    path("<slug:slug>/", product_detail, name="product_detail"),
]
