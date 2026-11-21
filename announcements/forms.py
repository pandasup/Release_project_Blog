
from django import forms

from .models import Announcement


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ('title', 'content', 'is_active')
        labels = {
            'title': 'Заголовок',
            'content': 'Текст',
            'is_active': 'Показувати на сайті',
        }

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if len(title) < 3:
            raise forms.ValidationError('Заголовок занадто короткий.')
        return title