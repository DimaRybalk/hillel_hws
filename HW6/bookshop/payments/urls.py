from django.urls import path
from .views import (
    CheckoutSession, 
    CustomerPortalView, 
    WebhookReceivedView, 
    PaymentSuccessView, 
    PaymentCancelView
)

urlpatterns = [
    path('checkout/', CheckoutSession.as_view(), name='checkout_session'),
    path('portal/', CustomerPortalView.as_view(), name='customer_portal'),
    path('webhook/', WebhookReceivedView.as_view(), name='stripe_webhook'),
    path('success/', PaymentSuccessView.as_view(), name='payment_success'),
    path('cancel/', PaymentCancelView.as_view(), name='payment_cancel'),
]