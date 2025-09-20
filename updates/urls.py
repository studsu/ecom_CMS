from django.urls import path
from . import views

app_name = 'updates'

urlpatterns = [
    path('ajax/check/', views.check_updates_ajax, name='ajax_check'),
]