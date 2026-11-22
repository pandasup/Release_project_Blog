from django.test import TestCase
from django.urls import reverse

from articles.models import Article, Category
from authentication.models import CustomUser
from core.testing_helpers import make_article, make_user

Status = Article.Status


class HomeViewTests(TestCase):
    def setUp(self):
        self.author = make_user('author1', CustomUser.Role.AUTHOR)
        self.url = reverse('main:home')

    def test_only_published_articles_are_listed(self):
        make_article(self.author, title='Опублікована')
        make_article(self.author, title='Чернетка', status=Status.DRAFT)
        response = self.client.get(self.url)
        titles = [a.title for a in response.context['articles']]
        self.assertIn('Опублікована', titles)
        self.assertNotIn('Чернетка', titles)

    def test_popular_articles_sorted_by_views(self):
        make_article(self.author, title='A', views_count=5)
        make_article(self.author, title='B', views_count=50)
        make_article(self.author, title='C', views_count=10)
        response = self.client.get(self.url)
        titles = [a.title for a in response.context['popular_articles']]
        self.assertEqual(titles, ['B', 'C', 'A'])

    def test_categories_widget_hides_categories_without_published_articles(self):
        with_published = Category.objects.create(name='З публікаціями', slug='pub')
        only_drafts = Category.objects.create(name='Лише чернетки', slug='drafts')
        make_article(self.author, category=with_published)
        make_article(self.author, status=Status.DRAFT, category=only_drafts)
        response = self.client.get(self.url)
        names = [c.name for c in response.context['categories']]
        self.assertEqual(names, ['З публікаціями'])

    def test_pagination(self):
        for i in range(7):
            make_article(self.author, title=f'Стаття {i}')
        first = self.client.get(self.url)
        second = self.client.get(self.url, {'page': 2})
        self.assertEqual(len(first.context['articles']), 6)
        self.assertEqual(len(second.context['articles']), 1)