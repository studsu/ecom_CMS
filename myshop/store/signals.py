# store/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Order

@receiver(pre_save, sender=Order)
def track_order_changes(sender, instance, **kwargs):
    """Track changes to order before saving"""
    if instance.pk:
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
            instance._old_tracking_id = old_instance.tracking_id
        except Order.DoesNotExist:
            instance._old_status = None
            instance._old_tracking_id = None
    else:
        instance._old_status = None
        instance._old_tracking_id = None

@receiver(post_save, sender=Order)
def send_order_update_notification(sender, instance, created, **kwargs):
    """Send email notification when order status or tracking ID is updated"""
    if created:
        return
    
    # Check if status changed to shipped or tracking ID was added/updated
    status_changed_to_shipped = (
        hasattr(instance, '_old_status') and 
        instance._old_status != 'shipped' and 
        instance.status == 'shipped'
    )
    
    tracking_id_updated = (
        hasattr(instance, '_old_tracking_id') and
        instance._old_tracking_id != instance.tracking_id and
        instance.tracking_id
    )
    
    if status_changed_to_shipped or tracking_id_updated:
        # Get customer email
        customer_email = instance.email or (instance.user.email if instance.user else None)
        
        if customer_email:
            # Prepare email context
            context = {
                'order': instance,
                'customer_name': instance.full_name or (instance.user.get_full_name() if instance.user else 'Customer'),
                'site_name': getattr(settings, 'SITE_NAME', 'SmokeKing'),
            }
            
            # Determine email subject and template based on what changed
            if status_changed_to_shipped and instance.tracking_id:
                subject = f'Your Order #{instance.id} Has Been Shipped!'
                template_name = 'emails/order_shipped_with_tracking.html'
            elif status_changed_to_shipped:
                subject = f'Your Order #{instance.id} Has Been Shipped!'
                template_name = 'emails/order_shipped.html'
            else:
                subject = f'Tracking Information Added for Order #{instance.id}'
                template_name = 'emails/tracking_updated.html'
            
            try:
                # Render HTML email
                html_message = render_to_string(template_name, context)
                plain_message = strip_tags(html_message)
                
                # Send email
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[customer_email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                # Log successful email send (optional)
                print(f"Order update email sent to {customer_email} for order #{instance.id}")
                
            except Exception as e:
                # Log email sending failure
                print(f"Failed to send order update email for order #{instance.id}: {str(e)}")