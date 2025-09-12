from django.urls import path
from .views import register_view, login_view, logout_view, profile_view, update_profile_view, order_detail_view

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    path('profile/', profile_view, name='profile'),
    path('update-profile/', update_profile_view, name='update_profile'),
    path('orders/<int:order_id>/', order_detail_view, name='order_detail'),

]

