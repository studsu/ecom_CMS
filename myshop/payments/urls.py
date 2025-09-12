# payments/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('start/', views.initiate_payment, name='initiate_payment'),
    path('callback/', views.phonepe_callback, name='phonepe_callback'),
    path('redirect/', views.payment_redirect, name='payment_redirect'),
    path('status/<str:merchant_order_id>/', views.check_order_status, name='check_order_status'),
    path('refund/<int:order_id>/', views.initiate_refund, name='initiate_refund'),
    path('refund/status/<str:merchant_refund_id>/', views.refund_status, name='refund_status'),
]
