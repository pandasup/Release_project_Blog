
from django.urls import path

from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('subscribe/', views.SubscribeView.as_view(), name='subscribe'),
    path('unsubscribe/', views.UnsubscribeView.as_view(), name='unsubscribe'),
]