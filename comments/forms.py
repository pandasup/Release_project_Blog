from django import forms

from .models import Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {'text': 'Коментар'}
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ваш коментар...'})
        }

    def clean_text(self):
        text = self.cleaned_data['text'].strip()
        if len(text) < 3:
            raise forms.ValidationError('Коментар занадто короткий (мінімум 3 символи).')
        if text.lower().count('http') > 2:
            raise forms.ValidationError('Забагато посилань у коментарі.')
        return text