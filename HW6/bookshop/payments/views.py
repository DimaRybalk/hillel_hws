import json
import os

from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
import stripe
from stripe import StripeClient

from order.models import Order

"""
Views for the `payments` app.

Handles the Stripe payment flow: creating Checkout Sessions, receiving
webhook events, and the success/cancel pages that update order status
and email a receipt once payment is confirmed.
"""

YOUR_DOMAIN = "http://localhost:8000/"


def get_stripe_client():
   
    api_key = os.environ.get(
        "STRIPE_CLIENT_API",
        getattr(settings, "STRIPE_CLIENT_API", "sk_test_placeholder_key_for_tests"),
    )
    return StripeClient(api_key)


class CheckoutSession(View):
    def post(self, request):
        client = get_stripe_client()
        try:
            order_id = request.POST.get("order_id")

            order = get_object_or_404(Order, id=order_id)
            stripe_amount = int(order.total_price * 100)

            checkout_session = client.v1.checkout.sessions.create(
                params={
                    "line_items": [
                        {
                            "price_data": {
                                "currency": "uah",
                                "product_data": {
                                    "name": f"Замовлення №{order.id} у магазині BookShop",
                                },
                                "unit_amount": stripe_amount,
                            },
                            "quantity": 1,
                        },
                    ],
                    "mode": "payment",
                    "success_url": YOUR_DOMAIN
                    + "payments/success/?session_id={CHECKOUT_SESSION_ID}",
                    "cancel_url": YOUR_DOMAIN + "payments/cancel/",
                    "metadata": {"order_id": str(order.id)},
                }
            )

            return redirect(checkout_session.url, code=303)
        except Exception as e:
            print(e)
            return HttpResponse("Server error", status=500)


class CustomerPortalView(View):
    def post(self, request):
        client = get_stripe_client()
        checkout_session_id = request.GET.get("session_id")
        checkout_session = client.v1.checkout.sessions.retrieve(
            checkout_session_id
        )

        return_url = YOUR_DOMAIN

        portalSession = client.v1.billing_portal.sessions.create(
            params={
                "customer": checkout_session.customer,
                "return_url": return_url,
            }
        )
        return redirect(portalSession.url, code=303)


@method_decorator(csrf_exempt, name="dispatch")
class WebhookReceivedView(View):
    def post(self, request):
        webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", None)
        request_data = json.loads(request.body)

        if webhook_secret:
            signature = request.headers.get("stripe-signature")
            try:
                event = stripe.Webhook.construct_event(
                    request.body, signature, webhook_secret
                )
                data = event["data"]
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=400)

            event_type = event["type"]
        else:
            data = request_data["data"]
            event_type = request_data["type"]

        data_object = data["object"]  # noqa: F841
        print("event " + event_type)

        return JsonResponse({"status": "success"})


class PaymentSuccessView(TemplateView):
    template_name = "success.html"

    def get(self, request, *args, **kwargs):
        client = get_stripe_client()
        session_id = request.GET.get("session_id")

        session = client.v1.checkout.sessions.retrieve(session_id)

        order_id = session.metadata.order_id
        order = get_object_or_404(Order, id=order_id)

        if order_id:
            order.status = "paid"
            order.save()

        customer_email = session.customer_details.email
        if customer_email:
            subject = (
                f"Електронний чек. Замовлення №{order.id} у магазині BookShop"
            )
            message = (
                f"Вітаємо! Ваша оплата успішно прийнята.\n\n"
                f"Деталі замовлення:\n"
                f"Номер замовлення: №{order.id}\n"
                f"Сума оплати: {order.total_price} грн.\n\n"
                f"Дякуємо, що обрали BookShop! Ваші книги вже готуються до відправки."
            )

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[customer_email],
                fail_silently=False,
            )

        return super().get(request, *args, **kwargs)


class PaymentCancelView(TemplateView):
    template_name = "cancel.html"