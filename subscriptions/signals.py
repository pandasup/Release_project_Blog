
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from articles.models import Article

from .emails import notify_subscribers


@receiver(post_save, sender=Article)
def article_published(sender, instance, **kwargs):
    if instance.status == Article.Status.PUBLISHED and not instance.subscribers_notified:

        def _notify():
            if notify_subscribers(instance.pk):
                instance.subscribers_notified = True  # синхронізуємо об'єкт у пам'яті

        transaction.on_commit(_notify)