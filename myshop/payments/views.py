# ✅ FIXED payments/views.py
from django.shortcuts import redirect, render, get_object_or_404
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseBadRequest
from store.models import Cart, Order, OrderItem
from .models import PhonePeOrder, PhonePeRefund
from uuid import uuid4
from phonepe.sdk.pg.env import Env
from phonepe.sdk.pg.payments.v2.standard_checkout_client import StandardCheckoutClient
from phonepe.sdk.pg.payments.v2.models.request.standard_checkout_pay_request import StandardCheckoutPayRequest
from phonepe.sdk.pg.common.models.request.meta_info import MetaInfo
from phonepe.sdk.pg.common.models.request.refund_request import RefundRequest
from phonepe.sdk.pg.common.exceptions import PhonePeException
import json

def get_phonepe_client():
    return StandardCheckoutClient.get_instance(
        client_id=settings.PHONEPE_CLIENT_ID,
        client_secret=settings.PHONEPE_CLIENT_SECRET,
        client_version=settings.PHONEPE_CLIENT_VERSION,
        env=Env.SANDBOX if settings.PHONEPE_ENV == 'SANDBOX' else Env.PRODUCTION,
        should_publish_events=False
    )

def initiate_payment(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.filter(is_saved=False)
    if not cart_items.exists():
        return redirect('view_cart')

    total = sum(item.quantity * item.product.price for item in cart_items)
    amount = int(total * 100)
    order = Order.objects.create(user=request.user, total_amount=total, shipping_address='TEMP', status='initiated')
    for item in cart_items:
        OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity, price=item.product.price)

    merchant_order_id = str(uuid4())
    PhonePeOrder.objects.create(order=order, merchant_order_id=merchant_order_id)

    client = get_phonepe_client()
    meta_info = MetaInfo(udf1=str(request.user.id))
    pay_request = StandardCheckoutPayRequest.build_request(
        merchant_order_id=merchant_order_id,
        amount=amount,
        redirect_url=settings.PHONEPE_REDIRECT_URL,
        callback_url=settings.PHONEPE_CALLBACK_URL,
        meta_info=meta_info
    )
    try:
        pay_response = client.pay(pay_request)
        return redirect(pay_response.redirect_url)
    except PhonePeException as e:
        return HttpResponse(f"Error: {e.message}", status=500)

# ✅ Place this in views.py
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import PhonePeOrder
from store.models import Order
from .views import get_phonepe_client
from phonepe.sdk.pg.common.exceptions import PhonePeException

def payment_redirect(request):
    latest_order = Order.objects.filter(user=request.user).order_by("-created_at").first()
    if not latest_order:
        return HttpResponse("No order found.")

    phonepe_order = PhonePeOrder.objects.filter(order=latest_order).first()
    if not phonepe_order:
        return HttpResponse("PhonePe order not found.")

    try:
        client = get_phonepe_client()
        status_response = client.get_order_status(phonepe_order.merchant_order_id)

        phonepe_order.status = status_response.state
        phonepe_order.save()

        status = status_response.state

        if status in ["CHECKOUT_ORDER_COMPLETED", "COMPLETED"]:
            latest_order.status = "paid"
            message = "✅ Payment successful! Your order has been confirmed."
        elif status in ["CHECKOUT_ORDER_FAILED", "FAILED", "CHECKOUT_TRANSACTION_ATTEMPT_FAILED"]:
            latest_order.status = "failed"
            message = "❌ Payment failed. Please try again or use another method."
        elif status in ["PENDING", "INITIATED"]:
            latest_order.status = "pending"
            message = "⏳ Your payment is still pending. We’ll confirm once it’s completed."
        else:
            latest_order.status = "unknown"
            message = f"⚠️ Unknown status received from PhonePe: {status}"

        latest_order.save()

    except PhonePeException as e:
        message = f"❌ Error while checking payment status: {e.message}"

    return render(request, "payments/result.html", {
        "message": message,
        "order": latest_order,
        "status": phonepe_order.status,
    })

@csrf_exempt
def phonepe_callback(request):
    try:
        client = get_phonepe_client()
        header_sig = request.headers.get('X-VERIFY', '')
        body = request.body.decode()

        cb = client.validate_callback(
            username=settings.PHONEPE_USERNAME,
            password=settings.PHONEPE_PASSWORD,
            callback_header_data=header_sig,
            callback_response_data=body
        )

        data = json.loads(body)
        event_type = data.get("type")
        merchant_order_id = cb.callback_data.merchant_order_id
        status = cb.callback_data.state

        phonepe_order = PhonePeOrder.objects.get(merchant_order_id=merchant_order_id)
        phonepe_order.status = status
        phonepe_order.save()

        if status in ["CHECKOUT_ORDER_COMPLETED", "COMPLETED"]:
            phonepe_order.order.status = "SUCCESS"
        elif status in ["FAILED", "CHECKOUT_ORDER_FAILED"]:
            phonepe_order.order.status = "failed"
        elif status in ["PENDING", "INITIATED"]:
            phonepe_order.order.status = "pending"
        else:
            phonepe_order.order.status = "unknown"

        phonepe_order.order.save()

        return HttpResponse("Callback processed")
    except PhonePeException as e:
        return HttpResponseBadRequest(e.message)


def check_order_status(request, merchant_order_id):
    client = get_phonepe_client()
    try:
        res = client.get_order_status(merchant_order_id, details=True)
        return HttpResponse(f"Order {merchant_order_id} status: {res.state}")
    except PhonePeException as e:
        return HttpResponseBadRequest(e.message)


def initiate_refund(request, order_id):
    phonepe_order = get_object_or_404(PhonePeOrder, order__id=order_id)
    client = get_phonepe_client()
    merchant_refund_id = str(uuid4())

    refund_req = RefundRequest.build_refund_request(
        merchant_refund_id=merchant_refund_id,
        original_merchant_order_id=phonepe_order.merchant_order_id,
        amount=int(phonepe_order.order.total_amount * 100)
    )

    try:
        refund_res = client.refund(refund_request=refund_req)
        PhonePeRefund.objects.create(
            phonepe_order=phonepe_order,
            merchant_refund_id=merchant_refund_id,
            refund_id=refund_res.refund_id,
            amount=refund_res.amount,
            status=refund_res.state
        )
        return HttpResponse(f"Refund initiated: {refund_res.state}")
    except PhonePeException as e:
        return HttpResponseBadRequest(e.message)


def refund_status(request, merchant_refund_id):
    client = get_phonepe_client()
    try:
        res = client.get_refund_status(merchant_refund_id)
        return HttpResponse(f"Refund Status: {res.state}")
    except PhonePeException as e:
        return HttpResponseBadRequest(e.message)
