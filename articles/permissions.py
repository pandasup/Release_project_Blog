from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class AuthorOrAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Створювати статті можуть автори та адміністратори."""

    def test_func(self):
        user = self.request.user
        return user.is_author or user.is_blog_admin


class OwnerOrAdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Редагувати й видаляти може власник статті або адміністратор."""

    def test_func(self):
        user = self.request.user
        article = self.get_object()
        return user.is_blog_admin or article.author_id == user.id