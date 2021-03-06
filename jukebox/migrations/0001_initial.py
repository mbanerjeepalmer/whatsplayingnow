# Generated by Django 2.0.3 on 2018-10-17 22:47

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_token', models.CharField(blank=True, max_length=255)),
                ('token_type', models.CharField(blank=True, max_length=255)),
                ('expires_at', models.FloatField(blank=True)),
                ('expires_in', models.FloatField(blank=True, null=True)),
                ('refresh_token', models.CharField(blank=True, max_length=255)),
                ('scope', models.CharField(blank=True, max_length=255)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
