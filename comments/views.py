from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from articles.models import Article

from .forms import CommentForm
from .models import Comment
from .permissions import can_moderate


class CommentCreateView(LoginRequiredMixin, View):
    http_method_names = ['post']

    def post(self, request, article_pk):
        article = get_object_or_404(
            Article, pk=article_pk, status=Article.Status.PUBLISHED
        )
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            comment.author = request.user
            comment.save()
            messages.success(request, 'Коментар додано.')
        else:
            for errors in form.errors.values():
                for error in errors:
                    messages.error(request, error)
        return redirect(f'{article.get_absolute_url()}#comments')


class CommentDeleteView(LoginRequiredMixin, View):
    http_method_names = ['post']

    def post(self, request, pk):
        comment = get_object_or_404(Comment.objects.select_related('article'), pk=pk)
        article = comment.article
        if not can_moderate(request.user, article):
            raise PermissionDenied
        comment.delete()
        messages.success(request, 'Коментар видалено.')
        return redirect(f'{article.get_absolute_url()}#comments')