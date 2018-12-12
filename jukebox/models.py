from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	access_token = models.CharField(max_length=255, blank=True)
	token_type = models.CharField(max_length=255, blank=True)
	expires_at = models.FloatField(blank=True)
	expires_in = models.FloatField(blank=True, null=True)
	refresh_token = models.CharField(max_length=255, blank=True)
	scope = models.CharField(max_length=255, blank=True)