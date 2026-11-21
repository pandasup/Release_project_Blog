from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Електронна пошта')

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email')

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Користувач з такою поштою вже існує.')
        return email
    
class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'bio', 'avatar')

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        exists = (
            CustomUser.objects.filter(email__iexact=email)
            .exclude(pk=self.instance.pk)
            .exists()
        )
        if exists:
            raise forms.ValidationError('Ця пошта вже використовується.')
        return email