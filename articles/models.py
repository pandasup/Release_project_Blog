from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg
from django.urls import reverse
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone
# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Чернетка'
        PUBLISHED = 'published', 'Опублікована'

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='articles'
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles'
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='articles')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    subscribers_notified = models.BooleanField(default=False, editable=False)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('articles:detail', kwargs={'pk': self.pk})

    @property
    def average_rating(self):
        return self.ratings.aggregate(avg=Avg('value'))['avg']

    def save(self, *args, **kwargs):
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

class Rating(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    value = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['article', 'user'], name='one_rating_per_user')
        ]


class ArticleMedia(models.Model):
    class MediaType(models.TextChoices):
        IMAGE = 'image', 'Фото'
        VIDEO = 'video', 'Відео'

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='articles/%Y/%m/')
    media_type = models.CharField(max_length=5, choices=MediaType.choices)
    caption = models.CharField(max_length=200, blank=True)
    
@receiver(post_delete, sender=ArticleMedia)
def delete_media_file(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(save=False)