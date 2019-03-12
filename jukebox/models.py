from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
	# TODO maybe the blanks should be nulls...
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	spotify_id = models.CharField(max_length=255, blank=True, unique=True)
	spotify_name = models.CharField(max_length=255, blank=True)
	access_token = models.CharField(max_length=255, blank=True)
	token_type = models.CharField(max_length=255, blank=True)
	expires_at = models.FloatField(blank=True)
	expires_in = models.FloatField(blank=True, null=True)
	refresh_token = models.CharField(max_length=255, blank=True)
	scope = models.CharField(max_length=255, blank=True)
