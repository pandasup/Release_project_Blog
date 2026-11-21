
from django.utils.text import slugify


def unique_slug(model, text, max_length=50):
    base = slugify(text, allow_unicode=True)[: max_length - 10] or model._meta.model_name
    slug, n = base, 1
    while model.objects.filter(slug=slug).exists():
        n += 1
        slug = f'{base}-{n}'
    return slug