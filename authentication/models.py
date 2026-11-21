from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        USER = 'user', 'Користувач'
        AUTHOR = 'author', 'Автор'
        ADMIN = 'admin', 'Адміністратор'

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    @property
    def is_author(self):
        return self.role == self.Role.AUTHOR

    @property
    def is_blog_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser