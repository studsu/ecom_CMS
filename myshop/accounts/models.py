from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models



class CustomUser(AbstractUser):
    phone = models.CharField(max_length=20)

from django.db import models
from django.conf import settings

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    shipping_address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
