from django.shortcuts import render, redirect
from django.db.models import Avg, Count, F, Q
from django.db import transaction
from django.http import Http404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from authentication.mixins import AdminRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from .forms import ArticleForm,ArticleMediaFormSet ,RatingForm, CategoryForm, TagForm
from .models import Article, Rating, Category, Tag
from .permissions import AuthorOrAdminRequiredMixin, OwnerOrAdminMixin
from comments.forms import CommentForm
from comments.permissions import can_moderate
# Create your views here.

class MediaFormsetMixin:
    """Додає до форми статті набір форм для фото й відео."""

    def get_media_formset(self):
        if not hasattr(self, '_media_formset'):
            args = (
                (self.request.POST, self.request.FILES)
                if self.request.method == 'POST'
                else ()
            )
            self._media_formset = ArticleMediaFormSet(*args, instance=self.object)
        return self._media_formset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['media_formset'] = self.get_media_formset()
        return context

    def form_valid(self, form):
        formset = self.get_media_formset()
        if not formset.is_valid():
            return self.form_invalid(form)
        with transaction.atomic():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
        messages.success(self.request, 'Статтю збережено.')
        return redirect(self.get_success_url())



class ArticleListView(ListView):
    template_name = 'articles/article_list.html'
    context_object_name = 'articles'
    paginate_by = 10

    def get_queryset(self):
        qs = (
            Article.objects.filter(status=Article.Status.PUBLISHED)
            .select_related('author', 'category')
            .prefetch_related('tags')
            .annotate(
                average_rating=Avg('ratings__value'), 
                rating_count=Count('ratings', distinct=True)
                
            )
        )
        if category := self.kwargs.get('category_slug'):
            qs = qs.filter(category__slug=category)
        if tag := self.kwargs.get('tag_slug'):
            qs = qs.filter(tags__slug=tag)
        return qs


class MyArticlesView(AuthorOrAdminRequiredMixin, ListView):
    template_name = 'articles/my_articles.html'
    context_object_name = 'articles'
    paginate_by = 10

    def get_queryset(self):
        return Article.objects.filter(author=self.request.user).select_related('category')


class ArticleDetailView(DetailView):
    model = Article
    template_name = 'articles/article_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        return (
            Article.objects.select_related('author', 'category')
            .prefetch_related('tags', 'media')
        )

    def get_object(self, queryset=None):
        article = super().get_object(queryset)
        user = self.request.user
        if article.status == Article.Status.PUBLISHED:
            Article.objects.filter(pk=article.pk).update(views_count=F('views_count') + 1)
        elif not (user.is_authenticated and (user.is_blog_admin or article.author_id == user.id)):
            raise Http404  # чернетки бачать лише власник і адмін
        return article

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.object
        user = self.request.user  # саме цього рядка не вистачало

        # коментарі
        context['comments'] = article.comments.select_related('author')
        context['comment_form'] = CommentForm()
        context['can_moderate'] = can_moderate(user, article)

        # оцінки
        stats = article.ratings.aggregate(avg=Avg('value'), count=Count('id'))
        context['rating_avg'] = stats['avg']
        context['rating_count'] = stats['count']

        user_rating = None
        if user.is_authenticated:
            user_rating = (
                article.ratings.filter(user=user).values_list('value', flat=True).first()
            )
        context['user_rating'] = user_rating
        context['rating_form'] = RatingForm(initial={'value': user_rating or 5})
        return context


class ArticleCreateView(AuthorOrAdminRequiredMixin, MediaFormsetMixin, CreateView):
    model = Article
    form_class = ArticleForm
    template_name = 'articles/article_form.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class ArticleUpdateView(OwnerOrAdminMixin, MediaFormsetMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = 'articles/article_form.html'


class ArticleDeleteView(OwnerOrAdminMixin, DeleteView):
    model = Article
    template_name = 'articles/article_confirm_delete.html'
    success_url = reverse_lazy('articles:list')
    
class RateArticleView(LoginRequiredMixin, View):
    http_method_names = ['post']

    def post(self, request, pk):
        article = get_object_or_404(Article, pk=pk, status=Article.Status.PUBLISHED)
        form = RatingForm(request.POST)
        if form.is_valid():
            Rating.objects.update_or_create(
                article=article,
                user=request.user,
                defaults={'value': form.cleaned_data['value']},
            )
            messages.success(request, 'Дякуємо за оцінку!')
        else:
            messages.error(request, 'Оберіть оцінку від 1 до 5.')
        return redirect(f'{article.get_absolute_url()}#rating')
    
# ---- базові класи ----
class TaxonomyListView(ListView):
    template_name = 'articles/taxonomy_list.html'
    list_title = ''
    create_url = update_url = delete_url = filter_url = ''

    def get_queryset(self):
        return self.model.objects.annotate(
            articles_count=Count(
                'articles', filter=Q(articles__status=Article.Status.PUBLISHED)
            )
        )


class TaxonomyCreateView(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = 'articles/taxonomy_form.html'
    success_message = 'Створено.'
    page_title = ''


class TaxonomyUpdateView(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    template_name = 'articles/taxonomy_form.html'
    success_message = 'Зміни збережено.'
    page_title = ''


class TaxonomyDeleteView(AdminRequiredMixin, SuccessMessageMixin, DeleteView):
    template_name = 'articles/taxonomy_confirm_delete.html'
    success_message = 'Видалено.'


# ---- категорії ----
class CategoryListView(TaxonomyListView):
    model = Category
    list_title = 'Категорії'
    create_url = 'articles:category_create'
    update_url = 'articles:category_update'
    delete_url = 'articles:category_delete'
    filter_url = 'articles:by_category'


class CategoryCreateView(TaxonomyCreateView):
    model = Category
    form_class = CategoryForm
    success_url = reverse_lazy('articles:categories')
    page_title = 'Нова категорія'


class CategoryUpdateView(TaxonomyUpdateView):
    model = Category
    form_class = CategoryForm
    success_url = reverse_lazy('articles:categories')
    page_title = 'Редагування категорії'


class CategoryDeleteView(TaxonomyDeleteView):
    model = Category
    success_url = reverse_lazy('articles:categories')


# ---- теги ----
class TagListView(TaxonomyListView):
    model = Tag
    list_title = 'Теги'
    create_url = 'articles:tag_create'
    update_url = 'articles:tag_update'
    delete_url = 'articles:tag_delete'
    filter_url = 'articles:by_tag'


class TagCreateView(TaxonomyCreateView):
    model = Tag
    form_class = TagForm
    success_url = reverse_lazy('articles:tags')
    page_title = 'Новий тег'


class TagUpdateView(TaxonomyUpdateView):
    model = Tag
    form_class = TagForm
    success_url = reverse_lazy('articles:tags')
    page_title = 'Редагування тега'


class TagDeleteView(TaxonomyDeleteView):
    model = Tag
    success_url = reverse_lazy('articles:tags')
    

