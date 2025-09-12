from django.apps import AppConfig

class ReviewsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "plugins.reviews"
    label = "plugins_reviews"  # distinct label so migrations are clean
    verbose_name = "Reviews"
