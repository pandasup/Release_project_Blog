from django.db.models import Avg, Count, Q
from django.views.generic import ListView

from articles.models import Article, Category, Tag


class HomeView(ListView):
    template_name = 'main/home.html'
    context_object_name = 'articles'
    paginate_by = 6

    @staticmethod
    def _published():
        return Article.objects.filter(status=Article.Status.PUBLISHED)

    def get_queryset(self):
        return (
            self._published()
            .select_related('author', 'category')
            .prefetch_related('tags')
            .annotate(
                avg_rating=Avg('ratings__value'),
                ratings_count=Count('ratings', distinct=True),
            )
            .order_by('-published_at', '-created_at')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        published_count = Count(
            'articles', filter=Q(articles__status=Article.Status.PUBLISHED)
        )

        # віджет «Популярні статті»: за кількістю переглядів
        context['popular_articles'] = self._published().order_by(
            '-views_count', '-published_at'
        )[:5]

        # віджети «Категорії» й «Теги»: лише ті, де є опубліковані статті
        context['categories'] = (
            Category.objects.annotate(articles_count=published_count)
            .filter(articles_count__gt=0)
            .order_by('-articles_count', 'name')[:10]
        )
        context['tags'] = (
            Tag.objects.annotate(articles_count=published_count)
            .filter(articles_count__gt=0)
            .order_by('-articles_count', 'name')[:20]
        )
        return context