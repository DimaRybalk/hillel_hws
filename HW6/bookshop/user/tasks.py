from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings



# Тут йде опис лише тасок які буде виконувати наш celery, виклик цих тасок буде робитись у вьюшках!

@shared_task  
def send_welcome_email_task(user_email, username):
    subject = "Ласкаво просимо до нашого книжкового магазину!"
    message = f"Привіт, {username}! Дякуємо за реєстрацію на нашому сайті."
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
        fail_silently=False,
    )
    return f"Email successfully sent to {user_email}"

