import logging
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView, LogoutView
from .forms import CustomUserCreationForm
from user.tasks import send_welcome_email_task

"""
Views for the `user` app.
 
Handles account registration, login, and logout via Django's built-in
auth views (Google OAuth is handled separately by django-allauth).
Logs authentication events for auditing.
"""


logger = logging.getLogger('user_logger')

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'user/register.html'
    success_url = reverse_lazy('books_list')

    def form_valid(self, form):
   
        response = super().form_valid(form)
        user = self.object
        
      
        logger.info(
            f"НОВИЙ КОРИСТУВАЧ: Зареєстровано новий акаунт через форму. "
            f"Username: {user.username}, Email: {user.email}, ID: {user.id}"
        )

        send_welcome_email_task.delay(user.email, user.username)

        return response


class CustomLoginView(LoginView):
    template_name = 'user/login.html'
    success_url = reverse_lazy('books_list')

    def form_valid(self, form):
      
        response = super().form_valid(form)
        user = self.request.user
        
        
        logger.info(
            f"АВТОРИЗАЦІЯ: Користувач {user.username} (ID: {user.id}) увійшов через форму."
        )
        return response
    
    def form_invalid(self, form):
       
        username = form.cleaned_data.get('username', 'Невідомо')
        logger.warning(
            f"ПОМИЛКА ВХОДУ: Невдала спроба авторизації для користувача '{username}'."
        )
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    success_url = reverse_lazy('login')

    def post(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            logger.info(
                f"ВИХІД: Користувач {user.username} (ID: {user.id}) вийшов із системи."
            )
        return super().post(request, *args, **kwargs)