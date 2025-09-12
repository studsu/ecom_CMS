from django.db import models
from django.conf import settings
from catalog.models import Product

class Review(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField()  # 1..5
    title = models.CharField(max_length=200, blank=True, default="")
    comment = models.TextField(blank=True, default="")
    is_public = models.BooleanField(default=True)  # can be moderated via admin
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "user"],
                name="unique_user_review_per_product",
            )
        ]

    def __str__(self):
        return f"{self.user} → {self.product} [{self.rating}]"
