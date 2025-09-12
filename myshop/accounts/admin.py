from django.contrib import admin
from .models import CustomUser
# Register your models here.
admin.site.site_header = "SmokeKing Admin"
admin.site.site_title = "SmokeKing Admin Portal"
admin.site.index_title = "Welcome to the SmokeKing Admin Portal"    

admin.site.register(CustomUser)