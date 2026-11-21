
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from .models import Subscription


def _next_url(request):
    next_url = request.POST.get('next', '')
    if url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return next_url
    return reverse('articles:list')


class SubscribeView(LoginRequiredMixin, View):
    http_method_names = ['post']

    def post(self, request):
        if not request.user.email:
            messages.error(request, 'Додайте електронну пошту в профілі, щоб підписатися.')
            return redirect('authentication:profile_edit')
        _, created = Subscription.objects.get_or_create(user=request.user)
        if created:
            messages.success(request, 'Ви підписалися на нові статті.')
        else:
            messages.info(request, 'Ви вже підписані.')
        return redirect(_next_url(request))


class UnsubscribeView(LoginRequiredMixin, View):
    http_method_names = ['post']

    def post(self, request):
        Subscription.objects.filter(user=request.user).delete()
        messages.success(request, 'Ви відписалися від розсилки.')
        return redirect(_next_url(request))