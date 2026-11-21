
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Доступ лише для адміністраторів блогу."""

    def test_func(self):
        return self.request.user.is_blog_admin