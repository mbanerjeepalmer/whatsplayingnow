from django.urls import path
from . import views

urlpatterns = [
    path('', views.tracks, name='tracks'),
    path('auth/', views.auth, name='auth'),
    path('callback/', views.callback, name='callback'),
]