from django.urls import path

from . import views

app_name = 'articles'

urlpatterns = [
    path('', views.ArticleListView.as_view(), name='list'),
    path('category/<str:category_slug>/', views.ArticleListView.as_view(), name='by_category'),
    path('tag/<str:tag_slug>/', views.ArticleListView.as_view(), name='by_tag'),
    path('my/', views.MyArticlesView.as_view(), name='my'),
    path('create/', views.ArticleCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ArticleDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ArticleUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.ArticleDeleteView.as_view(), name='delete'),
    path('<int:pk>/rate/', views.RateArticleView.as_view(), name='rate'),
    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),

    path('tags/', views.TagListView.as_view(), name='tags'),
    path('tags/create/', views.TagCreateView.as_view(), name='tag_create'),
    path('tags/<int:pk>/edit/', views.TagUpdateView.as_view(), name='tag_update'),
    path('tags/<int:pk>/delete/', views.TagDeleteView.as_view(), name='tag_delete'),
    ]