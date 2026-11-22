
from django.test import TestCase
from django.urls import reverse

from articles.models import Article
from authentication.models import CustomUser
from core.testing_helpers import make_article, make_user

from .models import Comment

Role = CustomUser.Role


class CommentCreateTests(TestCase):
    def setUp(self):
        self.author = make_user('author1', Role.AUTHOR)
        self.reader = make_user('reader')
        self.article = make_article(self.author)
        self.url = reverse('comments:add', args=[self.article.pk])

    def test_anonymous_cannot_comment(self):
        response = self.client.post(self.url, {'text': 'Привіт'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.count(), 0)

    def test_user_can_comment(self):
        self.client.force_login(self.reader)
        self.client.post(self.url, {'text': 'Чудова стаття'})
        comment = Comment.objects.get()
        self.assertEqual(comment.author, self.reader)
        self.assertEqual(comment.article, self.article)

    def test_invalid_comments_are_rejected(self):
        self.client.force_login(self.reader)
        bad_texts = [
            'ab',                                  # закороткий
            '   ',                                 # лише пробіли
            'http://a.com http://b.com http://c.com',  # забагато посилань
            'a' * 1001,                            # задовгий
        ]
        for text in bad_texts:
            self.client.post(self.url, {'text': text})
        self.assertEqual(Comment.objects.count(), 0)

    def test_cannot_comment_on_draft(self):
        draft = make_article(self.author, status=Article.Status.DRAFT)
        self.client.force_login(self.reader)
        response = self.client.post(reverse('comments:add', args=[draft.pk]), {'text': 'Привіт'})
        self.assertEqual(response.status_code, 404)


class CommentModerationTests(TestCase):
    def setUp(self):
        self.author = make_user('author1', Role.AUTHOR)
        self.other_author = make_user('author2', Role.AUTHOR)
        self.reader = make_user('reader')
        self.admin = make_user('admin1', Role.ADMIN)
        self.article = make_article(self.author)
        self.comment = Comment.objects.create(
            article=self.article, author=self.reader, text='Коментар'
        )
        self.url = reverse('comments:delete', args=[self.comment.pk])

    def test_article_author_can_delete(self):
        self.client.force_login(self.author)
        self.assertEqual(self.client.post(self.url).status_code, 302)
        self.assertFalse(Comment.objects.exists())

    def test_admin_can_delete(self):
        self.client.force_login(self.admin)
        self.client.post(self.url)
        self.assertFalse(Comment.objects.exists())

    def test_foreign_author_cannot_delete(self):
        self.client.force_login(self.other_author)
        self.assertEqual(self.client.post(self.url).status_code, 403)
        self.assertTrue(Comment.objects.exists())

    def test_regular_user_cannot_delete(self):
        self.client.force_login(self.reader)
        self.assertEqual(self.client.post(self.url).status_code, 403)
        self.assertTrue(Comment.objects.exists())

    def test_demoted_author_loses_moderation_rights(self):
        self.author.role = Role.USER
        self.author.save()
        self.client.force_login(self.author)
        self.assertEqual(self.client.post(self.url).status_code, 403)
        self.assertTrue(Comment.objects.exists())