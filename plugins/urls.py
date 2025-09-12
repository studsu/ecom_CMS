from django.urls import path
from .views import add_review

app_name = "plugins_reviews"

urlpatterns = [
    path("add/<slug:product_slug>/", add_review, name="add"),
]

