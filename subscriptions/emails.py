
import logging

from django.conf import settings
from django.core.mail import send_mass_mail

from articles.models import Article

from .models import Subscription

logger = logging.getLogger(__name__)


def notify_subscribers(article_pk):
    # Атомарно «забираємо» статтю: другий паралельний виклик нічого не знайде
    claimed = Article.objects.filter(
        pk=article_pk, subscribers_notified=False
    ).update(subscribers_notified=True)
    if not claimed:
        return

    article = Article.objects.select_related('author').get(pk=article_pk)
    subscriptions = (
        Subscription.objects.select_related('user')
        .filter(user__is_active=True)
        .exclude(user=article.author)
        .exclude(user__email='')
    )
    url = settings.SITE_URL + article.get_absolute_url()
    subject = f'Нова стаття: {article.title}'

    mails = tuple(
        (
            subject,
            (
                f'Вітаємо, {sub.user.get_username()}!\n\n'
                f'На блозі опубліковано нову статтю «{article.title}» '
                f'від {article.author.get_username()}.\n\n'
                f'Читати: {url}\n\n'
                'Відписатися можна на сторінці вашого профілю.'
            ),
            settings.DEFAULT_FROM_EMAIL,
            [sub.user.email],
        )
        for sub in subscriptions
    )
    if not mails:
        return
    try:
        send_mass_mail(mails)
    except Exception:
        logger.exception('Не вдалося розіслати листи про статтю %s', article_pk)