from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.urls import path, reverse_lazy

from . import views

app_name = 'authentication'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path(
        'login/',
        LoginView.as_view(
            template_name='authentication/login.html',
            redirect_authenticated_user=True,
        ),
        name='login',
    ),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    path(
        'password/',
        PasswordChangeView.as_view(
            template_name='authentication/password_change.html',
            success_url=reverse_lazy('authentication:profile'),
        ),
        name='password_change',
    ),
    path('authors/<str:username>/', views.AuthorProfileView.as_view(), name='author'),
]