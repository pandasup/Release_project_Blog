
from django.test import TestCase
from django.urls import reverse

from authentication.models import CustomUser
from core.testing_helpers import make_user

from .models import Announcement

Role = CustomUser.Role


class AnnouncementTests(TestCase):
    def setUp(self):
        self.admin = make_user('admin1', Role.ADMIN)
        self.author = make_user('author1', Role.AUTHOR)
        self.visible = Announcement.objects.create(title='Видиме', content='Текст', is_active=True)
        self.hidden = Announcement.objects.create(title='Приховане', content='Текст', is_active=False)

    def titles(self, response):
        return [a.title for a in response.context['announcements']]

    def test_public_sees_only_active(self):
        response = self.client.get(reverse('announcements:list'))
        self.assertEqual(self.titles(response), ['Видиме'])

    def test_admin_sees_hidden_too(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('announcements:list'))
        self.assertCountEqual(self.titles(response), ['Видиме', 'Приховане'])

    def test_only_admin_can_create(self):
        url = reverse('announcements:create')
        data = {'title': 'Нове', 'content': 'Текст', 'is_active': 'on'}

        self.assertEqual(self.client.post(url, data).status_code, 302)  # на вхід
        self.assertEqual(Announcement.objects.count(), 2)

        self.client.force_login(self.author)
        self.assertEqual(self.client.post(url, data).status_code, 403)
        self.assertEqual(Announcement.objects.count(), 2)

        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(url, data).status_code, 302)
        created = Announcement.objects.get(title='Нове')
        self.assertEqual(created.created_by, self.admin)

    def test_short_title_is_rejected(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse('announcements:create'), {'title': 'ab', 'content': 'Текст'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Announcement.objects.count(), 2)

    def test_admin_updates_and_deletes(self):
        self.client.force_login(self.admin)
        self.client.post(
            reverse('announcements:update', args=[self.visible.pk]),
            {'title': 'Оновлене', 'content': 'Текст', 'is_active': 'on'},
        )
        self.visible.refresh_from_db()
        self.assertEqual(self.visible.title, 'Оновлене')
        self.client.post(reverse('announcements:delete', args=[self.visible.pk]))
        self.assertFalse(Announcement.objects.filter(pk=self.visible.pk).exists())

    def test_author_cannot_delete(self):
        self.client.force_login(self.author)
        response = self.client.post(reverse('announcements:delete', args=[self.visible.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Announcement.objects.filter(pk=self.visible.pk).exists())