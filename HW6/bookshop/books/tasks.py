from celery import shared_task
from django.core.management import call_command
import time


# Викликається автоматично через налаштування в settings.py 

@shared_task
def clear_expired_sessions_task():
    call_command('clearsessions')
    return "sessions cleaned"

@shared_task
def generate_books_report_task():
    time.sleep(5) 
    report_data = "Report generated successfully"
    print("books report generated")
    return report_data