from django.urls import path
from . import views

app_name = 'hello_world'

urlpatterns = [
    path('message/', views.hello_world_message, name='message'),
    path('status/', views.plugin_status, name='status'),
]