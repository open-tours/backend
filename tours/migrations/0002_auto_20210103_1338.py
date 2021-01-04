# Generated by Django 3.1.4 on 2021-01-03 13:38

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import tours.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("tours", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="stage",
            name="cover_image",
            field=models.ImageField(blank=True, null=True, upload_to=tours.models.upload_to),
        ),
        migrations.AddField(
            model_name="stage", name="description", field=models.TextField(blank=True, max_length=102400, null=True),
        ),
        migrations.AddField(
            model_name="stage",
            name="owner",
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, to="users.user"),
            preserve_default=False,
        ),
    ]