from django.urls import path
from . import views

urlpatterns = [
	path('', views.tracks, name='home'), #TODO this is stupid, check optional parameter that doesn't user regex
	path('auth/', views.auth, name='auth'),
    path('t/<str:spotify_id>', views.tracks, name='view_tracks'),
    path('callback/', views.callback, name='callback'),
]
