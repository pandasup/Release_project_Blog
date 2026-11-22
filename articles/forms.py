from django import forms
from django.utils import timezone
from django.utils.text import slugify
from .models import Article, ArticleMedia, Category, Rating, Tag
from .utils import unique_slug
from pathlib import Path
from django.core.files.uploadedfile import UploadedFile
from django.forms import inlineformset_factory
from PIL import Image



class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'content', 'category', 'tags', 'status']
        widgets = {'tags': forms.CheckboxSelectMultiple}

    @staticmethod
    def _unique_slug(title):
        base = slugify(title, allow_unicode=True)[:40] or 'article'
        slug, n = base, 1
        while Article.objects.filter(slug=slug).exists():
            n += 1
            slug = f'{base}-{n}'
        return slug

    def save(self, commit=True):
        article = super().save(commit=False)
        if not article.slug:
            article.slug = self._unique_slug(article.title)
        if article.status == Article.Status.PUBLISHED and article.published_at is None:
            article.published_at = timezone.now()
        if commit:
            article.save()
            self.save_m2m()
        return article
    
class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ('value',)
        labels = {'value': 'Ваша оцінка'}
        widgets = {
            'value': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)])
        }
        
class TaxonomyForm(forms.ModelForm):
    """Базова форма для категорій і тегів."""

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        qs = self._meta.model.objects.all()
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        existing = {n.casefold() for n in qs.values_list('name', flat=True)}
        if name.casefold() in existing:
            raise forms.ValidationError('Така назва вже існує.')
        return name

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.slug:
            obj.slug = unique_slug(self._meta.model, obj.name)
        if commit:
            obj.save()
        return obj


class CategoryForm(TaxonomyForm):
    class Meta:
        model = Category
        fields = ('name',)
        labels = {'name': 'Назва категорії'}



class TagForm(TaxonomyForm):
    class Meta:
        model = Tag
        fields = ('name',)
        labels = {'name': 'Назва тега'}


    
IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
VIDEO_EXTENSIONS = {'mp4', 'webm', 'ogg'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024    # 5 МБ
MAX_VIDEO_SIZE = 50 * 1024 * 1024   # 50 МБ


class ArticleMediaForm(forms.ModelForm):
    class Meta:
        model = ArticleMedia
        fields = ('file', 'caption')
        labels = {'file': 'Файл (фото або відео)', 'caption': 'Підпис'}

    def clean_file(self):
        file = self.cleaned_data.get('file')
        # при редагуванні без нового файлу тут лежить уже збережений файл
        if not isinstance(file, UploadedFile):
            return file

        ext = Path(file.name).suffix.lower().lstrip('.')
        if ext in IMAGE_EXTENSIONS:
            if file.size > MAX_IMAGE_SIZE:
                raise forms.ValidationError('Зображення завелике (максимум 5 МБ).')
            try:
                Image.open(file).verify()
            except Exception:
                raise forms.ValidationError('Файл не є коректним зображенням.')
            file.seek(0)
            self.detected_type = ArticleMedia.MediaType.IMAGE
        elif ext in VIDEO_EXTENSIONS:
            if file.size > MAX_VIDEO_SIZE:
                raise forms.ValidationError('Відео завелике (максимум 50 МБ).')
            self.detected_type = ArticleMedia.MediaType.VIDEO
        else:
            raise forms.ValidationError(
                'Дозволені формати: jpg, jpeg, png, gif, webp, mp4, webm, ogg.'
            )
        return file

    def save(self, commit=True):
        obj = super().save(commit=False)
        detected = getattr(self, 'detected_type', None)
        if detected:
            obj.media_type = detected
        if commit:
            obj.save()
        return obj


ArticleMediaFormSet = inlineformset_factory(
    Article,
    ArticleMedia,
    form=ArticleMediaForm,
    extra=3,
    max_num=10,
    validate_max=True,
    can_delete=True,
)