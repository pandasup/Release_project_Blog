
from django.test import TestCase
from django.urls import reverse

from core.testing_helpers import PASSWORD, make_user

from .models import CustomUser

Role = CustomUser.Role


class RegistrationTests(TestCase):
    def data(self, **extra):
        data = {
            'username': 'newbie',
            'email': 'newbie@example.com',
            'password1': PASSWORD,
            'password2': PASSWORD,
        }
        data.update(extra)
        return data

    def test_registration_creates_user_and_logs_in(self):
        response = self.client.post(reverse('authentication:register'), self.data())
        self.assertRedirects(response, reverse('articles:list'), fetch_redirect_response=False)
        user = CustomUser.objects.get(username='newbie')
        self.assertEqual(user.role, Role.USER)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_role_cannot_be_injected_through_form(self):
        self.client.post(reverse('authentication:register'), self.data(role='admin'))
        self.assertEqual(CustomUser.objects.get(username='newbie').role, Role.USER)

    def test_duplicate_email_is_rejected_case_insensitively(self):
        make_user('exists', email='exists@example.com')
        response = self.client.post(
            reverse('authentication:register'),
            self.data(email='Exists@Example.com'),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CustomUser.objects.count(), 1)

    def test_weak_password_is_rejected(self):
        response = self.client.post(
            reverse('authentication:register'),
            self.data(password1='12345678', password2='12345678'),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(username='newbie').exists())

    def test_logged_in_user_is_redirected_from_register(self):
        self.client.force_login(make_user('reader'))
        response = self.client.get(reverse('authentication:register'))
        self.assertRedirects(response, reverse('articles:list'), fetch_redirect_response=False)


class ProfileTests(TestCase):
    def setUp(self):
        self.user = make_user('reader')
        self.edit_url = reverse('authentication:profile_edit')

    def profile_data(self, **extra):
        data = {
            'first_name': 'Іван',
            'last_name': 'Петренко',
            'email': 'reader@example.com',
            'bio': 'Про себе',
        }
        data.update(extra)
        return data

    def test_profile_requires_login(self):
        url = reverse('authentication:profile')
        response = self.client.get(url)
        self.assertRedirects(
            response,
            f"{reverse('authentication:login')}?next={url}",
            fetch_redirect_response=False,
        )

    def test_user_edits_own_data(self):
        self.client.force_login(self.user)
        response = self.client.post(self.edit_url, self.profile_data())
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Іван')

    def test_role_cannot_be_changed_through_profile(self):
        self.client.force_login(self.user)
        self.client.post(self.edit_url, self.profile_data(role='admin'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, Role.USER)

    def test_cannot_take_email_of_another_user(self):
        make_user('other', email='other@example.com')
        self.client.force_login(self.user)
        response = self.client.post(self.edit_url, self.profile_data(email='OTHER@example.com'))
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'reader@example.com')

    def test_password_change_keeps_user_logged_in(self):
        self.client.force_login(self.user)
        new_password = 'N3w-Str0ng-pass-456'
        response = self.client.post(
            reverse('authentication:password_change'),
            {
                'old_password': PASSWORD,
                'new_password1': new_password,
                'new_password2': new_password,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))
        self.assertIn('_auth_user_id', self.client.session)

    def test_public_page_only_for_authors_and_admins(self):
        make_user('writer', Role.AUTHOR)
        ok = self.client.get(reverse('authentication:author', args=['writer']))
        not_found = self.client.get(reverse('authentication:author', args=['reader']))
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(not_found.status_code, 404)