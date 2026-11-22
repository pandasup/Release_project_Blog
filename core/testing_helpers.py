
import uuid
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from articles.models import Article

User = get_user_model()
PASSWORD = 'Str0ng-pass-123'


def make_user(username, role=None, email=None):
    if email is None:
        email = f'{username}@example.com'
    return User.objects.create_user(
        username=username,
        email=email,
        password=PASSWORD,
        role=role or User.Role.USER,
    )


def make_article(author, title='Тестова стаття', status=Article.Status.PUBLISHED, **extra):
    return Article.objects.create(
        title=title,
        slug=f'a-{uuid.uuid4().hex[:12]}',
        content='Текст статті',
        author=author,
        status=status,
        **extra,
    )


def make_image(name='photo.png'):
    buffer = BytesIO()
    Image.new('RGB', (10, 10), 'red').save(buffer, format='PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')