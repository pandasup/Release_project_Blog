from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect
from django.views.generic import CreateView, DetailView, UpdateView, TemplateView

from articles.models import Article

from .forms import RegistrationForm, ProfileForm
from .models import CustomUser


class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = 'authentication/register.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('articles:list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, 'Реєстрація пройшла успішно. Ласкаво просимо!')
        return redirect('articles:list')
    
class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'authentication/profile.html'


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    form_class = ProfileForm
    template_name = 'authentication/profile_edit.html'
    success_url = reverse_lazy('authentication:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Профіль оновлено.')
        return super().form_valid(form)


class AuthorProfileView(DetailView):
    template_name = 'authentication/author_profile.html'
    context_object_name = 'author'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_queryset(self):
        # публічні сторінки лише в авторів та адміністраторів
        return CustomUser.objects.filter(
            role__in=[CustomUser.Role.AUTHOR, CustomUser.Role.ADMIN]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['articles'] = self.object.articles.filter(
            status=Article.Status.PUBLISHED
        ).select_related('category')
        return context