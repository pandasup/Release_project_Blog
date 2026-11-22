
import os
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from authentication.models import CustomUser
from core.testing_helpers import make_article, make_image, make_user

from .models import Article, ArticleMedia, Category, Rating, Tag

Role = CustomUser.Role
Status = Article.Status

EMPTY_MEDIA = {
    'media-TOTAL_FORMS': '0',
    'media-INITIAL_FORMS': '0',
    'media-MIN_NUM_FORMS': '0',
    'media-MAX_NUM_FORMS': '10',
}


def article_data(**extra):
    data = {'title': 'Нова стаття', 'content': 'Текст', 'status': 'published', **EMPTY_MEDIA}
    data.update(extra)
    return data


class ArticleAccessTests(TestCase):
    def setUp(self):
        self.author = make_user('author1', Role.AUTHOR)
        self.other_author = make_user('author2', Role.AUTHOR)
        self.user = make_user('reader', Role.USER)
        self.admin = make_user('admin1', Role.ADMIN)
        self.article = make_article(self.author)
        self.update_url = reverse('articles:update', args=[self.article.pk])
        self.delete_url = reverse('articles:delete', args=[self.article.pk])

    # --- створення ---
    def test_anonymous_is_redirected_to_login(self):
        url = reverse('articles:create')
        response = self.client.get(url)
        self.assertRedirects(
            response,
            f"{reverse('authentication:login')}?next={url}",
            fetch_redirect_response=False,
        )

    def test_regular_user_cannot_create(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('articles:create'), article_data())
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Article.objects.count(), 1)

    def test_author_creates_article(self):
        self.client.force_login(self.author)
        response = self.client.post(reverse('articles:create'), article_data())
        self.assertEqual(response.status_code, 302)
        article = Article.objects.get(title='Нова стаття')
        self.assertEqual(article.author, self.author)
        self.assertTrue(article.slug)
        self.assertIsNotNone(article.published_at)

    def test_draft_has_no_publication_date(self):
        self.client.force_login(self.author)
        self.client.post(reverse('articles:create'), article_data(status='draft'))
        self.assertIsNone(Article.objects.get(title='Нова стаття').published_at)

    # --- редагування ---
    def test_owner_edits_own_article(self):
        self.client.force_login(self.author)
        response = self.client.post(self.update_url, article_data(title='Змінено'))
        self.assertEqual(response.status_code, 302)
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, 'Змінено')

    def test_author_cannot_edit_foreign_article(self):
        self.client.force_login(self.other_author)
        response = self.client.post(self.update_url, article_data(title='Злам'))
        self.assertEqual(response.status_code, 403)
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, 'Тестова стаття')

    def test_admin_edits_any_article(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.update_url, article_data(title='Від адміна'))
        self.assertEqual(response.status_code, 302)
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, 'Від адміна')

    # --- видалення ---
    def test_author_cannot_delete_foreign_article(self):
        self.client.force_login(self.other_author)
        self.assertEqual(self.client.post(self.delete_url).status_code, 403)
        self.assertTrue(Article.objects.filter(pk=self.article.pk).exists())

    def test_owner_deletes_own_article(self):
        self.client.force_login(self.author)
        self.client.post(self.delete_url)
        self.assertFalse(Article.objects.filter(pk=self.article.pk).exists())

    def test_admin_deletes_any_article(self):
        self.client.force_login(self.admin)
        self.client.post(self.delete_url)
        self.assertFalse(Article.objects.filter(pk=self.article.pk).exists())

    # --- видимість чернеток (потрібен шаблон article_detail.html) ---
    def test_draft_visibility(self):
        draft = make_article(self.author, status=Status.DRAFT)
        url = reverse('articles:detail', args=[draft.pk])

        self.assertEqual(self.client.get(url).status_code, 404)  # анонім

        self.client.force_login(self.user)
        self.assertEqual(self.client.get(url).status_code, 404)  # чужий

        self.client.force_login(self.author)
        self.assertEqual(self.client.get(url).status_code, 200)  # власник

        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(url).status_code, 200)  # адмін

    def test_views_counter_increments(self):
        url = reverse('articles:detail', args=[self.article.pk])
        self.client.get(url)
        self.client.get(url)
        self.article.refresh_from_db()
        self.assertEqual(self.article.views_count, 2)


TEMP_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ArticleMediaTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.author = make_user('author1', Role.AUTHOR)
        self.client.force_login(self.author)

    def post_with_file(self, upload):
        data = article_data(status='draft')
        data.update({
            'media-TOTAL_FORMS': '1',
            'media-0-file': upload,
            'media-0-caption': 'Підпис',
        })
        return self.client.post(reverse('articles:create'), data)

    def test_valid_image_is_saved_with_detected_type(self):
        response = self.post_with_file(make_image())
        self.assertEqual(response.status_code, 302)
        media = ArticleMedia.objects.get()
        self.assertEqual(media.media_type, ArticleMedia.MediaType.IMAGE)

    def test_text_file_is_rejected(self):
        upload = SimpleUploadedFile('notes.txt', b'hello', content_type='text/plain')
        response = self.post_with_file(upload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ArticleMedia.objects.count(), 0)
        self.assertEqual(Article.objects.count(), 0)  # транзакція: статті теж немає

    def test_fake_image_is_rejected(self):
        upload = SimpleUploadedFile('fake.png', b'not an image', content_type='image/png')
        response = self.post_with_file(upload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ArticleMedia.objects.count(), 0)

    def test_file_is_removed_from_disk_with_record(self):
        self.post_with_file(make_image())
        media = ArticleMedia.objects.get()
        path = media.file.path
        self.assertTrue(os.path.exists(path))
        media.delete()
        self.assertFalse(os.path.exists(path))


class RatingTests(TestCase):
    def setUp(self):
        self.author = make_user('author1', Role.AUTHOR)
        self.user1 = make_user('reader1')
        self.user2 = make_user('reader2')
        self.article = make_article(self.author)

    def rate(self, value, article=None):
        article = article or self.article
        return self.client.post(reverse('articles:rate', args=[article.pk]), {'value': value})

    def test_anonymous_cannot_rate(self):
        response = self.rate(5)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Rating.objects.count(), 0)

    def test_second_rating_updates_the_first(self):
        self.client.force_login(self.user1)
        self.rate(3)
        self.rate(5)
        self.assertEqual(Rating.objects.count(), 1)
        self.assertEqual(Rating.objects.get().value, 5)

    def test_invalid_values_are_rejected(self):
        self.client.force_login(self.user1)
        for value in ('0', '6', 'abc', ''):
            self.rate(value)
        self.assertEqual(Rating.objects.count(), 0)

    def test_cannot_rate_draft(self):
        draft = make_article(self.author, status=Status.DRAFT)
        self.client.force_login(self.user1)
        self.assertEqual(self.rate(5, draft).status_code, 404)

    def test_average_rating(self):
        self.client.force_login(self.user1)
        self.rate(4)
        self.client.force_login(self.user2)
        self.rate(2)
        self.assertEqual(self.article.average_rating, 3)


class CategoryTagTests(TestCase):
    def setUp(self):
        self.admin = make_user('admin1', Role.ADMIN)
        self.author = make_user('author1', Role.AUTHOR)

    def test_admin_creates_category_with_generated_slug(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('articles:category_create'), {'name': 'Технології'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Category.objects.get().slug, 'технології')

    def test_slug_collisions_get_suffix(self):
        self.client.force_login(self.admin)
        for name in ('C++', 'C#'):
            self.client.post(reverse('articles:category_create'), {'name': name})
        slugs = sorted(Category.objects.values_list('slug', flat=True))
        self.assertEqual(slugs, ['c', 'c-2'])

    def test_duplicate_name_is_rejected_ignoring_case(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('articles:category_create'), {'name': 'Технології'})
        response = self.client.post(reverse('articles:category_create'), {'name': 'технології'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Category.objects.count(), 1)

    def test_non_admin_cannot_manage_taxonomy(self):
        self.client.force_login(self.author)
        response = self.client.post(reverse('articles:tag_create'), {'name': 'django'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Tag.objects.count(), 0)

    def test_deleting_category_keeps_articles(self):
        category = Category.objects.create(name='Тест', slug='test')
        article = make_article(self.author, category=category)
        self.client.force_login(self.admin)
        self.client.post(reverse('articles:category_delete', args=[category.pk]))
        article.refresh_from_db()
        self.assertIsNone(article.category)

    def test_deleting_tag_keeps_articles(self):
        tag = Tag.objects.create(name='django', slug='django')
        article = make_article(self.author)
        article.tags.add(tag)
        self.client.force_login(self.admin)
        self.client.post(reverse('articles:tag_delete', args=[tag.pk]))
        self.assertTrue(Article.objects.filter(pk=article.pk).exists())
        self.assertEqual(article.tags.count(), 0)