
from django.conf import settings
from django.db import models


class Subscription(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Підписка: {self.user}'