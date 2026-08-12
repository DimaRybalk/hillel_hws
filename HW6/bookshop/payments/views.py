import json
import os

from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
import stripe
from stripe import StripeClient

from order.models import Order
import logging

"""
Views for the `payments` app.

Handles the Stripe payment flow: creating Checkout Sessions, receiving
webhook events, and the success/cancel pages that update order status
and email a receipt once payment is confirmed.
"""

# 1. Отримуємо ключ із env або settings. Якщо ключа немає — беремо тестовий заповнювач для Stripe SDK
api_key = os.environ.get(
    "STRIPE_CLIENT_API",
    getattr(settings, "STRIPE_CLIENT_API", "sk_test_placeholder_key_for_tests"),
)

logger = logging.getLogger(__name__)

# 2. Оголошуємо client прямо у модулі
client = StripeClient(api_key)


class CheckoutSession(View):
    def post(self, request):
        try:
            order_id = request.POST.get("order_id")

            order = get_object_or_404(Order, id=order_id)
            stripe_amount = int(order.total_price * 100)

            # Отримуємо повні абсолютні URL з урахуванням домену та локалі (/uk/...)
            success_url = (
                request.build_absolute_uri(reverse("payment_success"))
                + "?session_id={CHECKOUT_SESSION_ID}"
            )
            cancel_url = request.build_absolute_uri(reverse("payment_cancel"))

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
                    "success_url": success_url,
                    "cancel_url": cancel_url,
                    "metadata": {"order_id": str(order.id)},
                }
            )

            return redirect(checkout_session.url, code=303)
        except Exception as e:
            print(e)
            return HttpResponse("Server error", status=500)


class CustomerPortalView(View):
    def post(self, request):
        checkout_session_id = request.GET.get("session_id")
        checkout_session = client.v1.checkout.sessions.retrieve(checkout_session_id)

        return_url = request.build_absolute_uri(reverse("books_list"))

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
        session_id = request.GET.get("session_id")

        if session_id:
            try:
                session = client.v1.checkout.sessions.retrieve(session_id)

                metadata = getattr(session, "metadata", {}) or {}
                order_id = (
                    metadata.get("order_id")
                    if isinstance(metadata, dict)
                    else getattr(metadata, "order_id", None)
                )

                if order_id:
                    order = get_object_or_404(Order, id=order_id)
                    order.status = "paid"
                    order.save()

                    customer_details = getattr(session, "customer_details", None)
                    customer_email = None
                    if customer_details:
                        customer_email = getattr(customer_details, "email", None) or (
                            customer_details.get("email")
                            if isinstance(customer_details, dict)
                            else None
                        )

                    if customer_email:
                        try:
                            subject = f"Електронний чек. Замовлення №{order.id} у магазині BookShop"
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
                                fail_silently=True,
                            )
                        except Exception as mail_err:
                            logger.error(f"Помилка відправки листа: {mail_err}")

            except Exception as e:
                logger.error(f"Помилка обробки успішної оплати: {e}")

        return super().get(request, *args, **kwargs)


class PaymentCancelView(TemplateView):
    template_name = "cancel.html"
