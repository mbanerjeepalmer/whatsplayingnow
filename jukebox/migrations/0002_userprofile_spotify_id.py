# Generated by Django 2.1.4 on 2019-01-28 22:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jukebox', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='spotify_id',
            field=models.CharField(blank=True, max_length=255, unique=True),
        ),
    ]