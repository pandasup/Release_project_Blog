
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from articles.models import Article
from authentication.models import CustomUser
from core.testing_helpers import make_article, make_user

from .models import Subscription

Role = CustomUser.Role
Status = Article.Status


class SubscribeViewTests(TestCase):
    def setUp(self):
        self.user = make_user('reader')

    def test_anonymous_is_redirected(self):
        response = self.client.post(reverse('subscriptions:subscribe'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Subscription.objects.count(), 0)

    def test_subscribe_is_idempotent_and_unsubscribe_works(self):
        self.client.force_login(self.user)
        self.client.post(reverse('subscriptions:subscribe'))
        self.client.post(reverse('subscriptions:subscribe'))
        self.assertEqual(Subscription.objects.count(), 1)
        self.client.post(reverse('subscriptions:unsubscribe'))
        self.assertEqual(Subscription.objects.count(), 0)

    def test_user_without_email_cannot_subscribe(self):
        user = make_user('noemail', email='')
        self.client.force_login(user)
        response = self.client.post(reverse('subscriptions:subscribe'))
        self.assertRedirects(
            response, reverse('authentication:profile_edit'), fetch_redirect_response=False
        )
        self.assertEqual(Subscription.objects.count(), 0)

    def test_next_parameter_is_validated(self):
        self.client.force_login(self.user)
        evil = self.client.post(
            reverse('subscriptions:subscribe'), {'next': 'https://evil.example/'}
        )
        self.assertRedirects(evil, reverse('articles:list'), fetch_redirect_response=False)
        good = self.client.post(
            reverse('subscriptions:unsubscribe'), {'next': '/articles/tags/'}
        )
        self.assertRedirects(good, '/articles/tags/', fetch_redirect_response=False)


class SubscriptionEmailTests(TestCase):
    def setUp(self):
        self.author = make_user('author1', Role.AUTHOR)
        self.reader = make_user('reader')
        Subscription.objects.create(user=self.reader)

    def save_article(self, article):
        """Зберігає статтю й виконує відкладені on_commit-розсилки."""
        with self.captureOnCommitCallbacks(execute=True):
            article.save()

    def new_draft(self):
        with self.captureOnCommitCallbacks(execute=True):
            return make_article(self.author, status=Status.DRAFT)

    def test_draft_sends_nothing(self):
        self.new_draft()
        self.assertEqual(len(mail.outbox), 0)

    def test_publish_sends_one_mail_to_subscriber(self):
        article = self.new_draft()
        article.status = Status.PUBLISHED
        self.save_article(article)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ['reader@example.com'])
        self.assertIn(article.title, message.subject)
        self.assertIn(article.get_absolute_url(), message.body)

    def test_article_created_as_published_sends_mail(self):
        with self.captureOnCommitCallbacks(execute=True):
            make_article(self.author)
        self.assertEqual(len(mail.outbox), 1)

    def test_no_duplicate_mails_on_edit_or_republish(self):
        article = self.new_draft()
        article.status = Status.PUBLISHED
        self.save_article(article)

        article.title = 'Нова назва'
        self.save_article(article)
        article.status = Status.DRAFT
        self.save_article(article)
        article.status = Status.PUBLISHED
        self.save_article(article)

        self.assertEqual(len(mail.outbox), 1)

    def test_author_is_not_notified_about_own_article(self):
        Subscription.objects.create(user=self.author)
        with self.captureOnCommitCallbacks(execute=True):
            make_article(self.author)
        self.assertEqual([m.to for m in mail.outbox], [['reader@example.com']])

    def test_unsubscribed_and_inactive_users_get_nothing(self):
        Subscription.objects.all().delete()
        inactive = make_user('inactive')
        inactive.is_active = False
        inactive.save()
        Subscription.objects.create(user=inactive)
        with self.captureOnCommitCallbacks(execute=True):
            make_article(self.author)
        self.assertEqual(len(mail.outbox), 0)

    def test_each_subscriber_gets_a_separate_mail(self):
        Subscription.objects.create(user=make_user('reader2'))
        with self.captureOnCommitCallbacks(execute=True):
            make_article(self.author)
        self.assertEqual(len(mail.outbox), 2)
        self.assertTrue(all(len(m.to) == 1 for m in mail.outbox))