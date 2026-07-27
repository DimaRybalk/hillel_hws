from unittest.mock import patch, MagicMock
from django.core import mail
from django.urls import reverse
from django.test import Client
import pytest
from order.models import Order
from books.models import Book
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
@patch('payments.views.client') 
def test_payment_success_sends_email_and_updates_order(mock_stripe_client):
    user = User.objects.create_user(username='buyer', email='buyer@example.com', password='password123')
    order = Order.objects.create(user=user, total_price=500.00, status='new')
    mock_session = MagicMock()
    mock_session.metadata.order_id = order.id
    mock_session.customer_details.email = 'buyer@example.com'
    mock_stripe_client.v1.checkout.sessions.retrieve.return_value = mock_session
    client = Client()
    client.login(username='buyer', password='password123')

    success_url = reverse('payment_success')
    response = client.get(f"{success_url}?session_id=cs_test_123")

    assert response.status_code == 200
    order.refresh_from_db()
    assert order.status == 'paid'

    assert len(mail.outbox) == 1
    sent_email = mail.outbox[0]
    
    assert sent_email.to == ['buyer@example.com']
    assert f'Замовлення №{order.id}' in sent_email.subject
    assert '500.00 грн.' in sent_email.body