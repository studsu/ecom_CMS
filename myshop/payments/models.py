# payments/models.py
from django.db import models
from store.models import Order

class PhonePeOrder(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    merchant_order_id = models.CharField(max_length=64, unique=True)
    phonepe_order_id = models.CharField(max_length=128, blank=True, null=True)
    status = models.CharField(max_length=50, default='INITIATED')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.merchant_order_id} - {self.status}"


class PhonePeRefund(models.Model):
    phonepe_order = models.ForeignKey(PhonePeOrder, on_delete=models.CASCADE)
    merchant_refund_id = models.CharField(max_length=64, unique=True)
    refund_id = models.CharField(max_length=128, blank=True, null=True)
    amount = models.PositiveIntegerField()
    status = models.CharField(max_length=50, default='INITIATED')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Refund {self.merchant_refund_id} - {self.status}"
