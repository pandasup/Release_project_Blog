from django.contrib import admin

from .models import Article, ArticleMedia, Category, Rating, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}




class ArticleMediaInline(admin.TabularInline):
    model = ArticleMedia
    extra = 1

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'category', 'created_at')
    list_filter = ('status', 'category')
    search_fields = ('title', 'content')
    inlines = [ArticleMediaInline]


admin.site.register(Rating)
