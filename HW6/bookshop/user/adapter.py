import logging
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

logger = logging.getLogger("user_logger")


class MyCustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        if not user.username or len(user.username) <= 1:
            if user.email:
                user.username = user.email.split("@")[0]
            else:
                user.username = f"user_{sociallogin.account.uid[:8]}"

        logger.info(
            f"НОВИЙ КОРИСТУВАЧ (GOOGLE): Зареєстровано через Google. "
            f"Username: {user.username}, Email: {user.email}, ID: {user.id}"
        )

        return user
