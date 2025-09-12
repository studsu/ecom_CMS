# admin.py
from django.contrib import admin
from .models import PhonePeOrder, PhonePeRefund

admin.site.register(PhonePeOrder)
admin.site.register(PhonePeRefund)
