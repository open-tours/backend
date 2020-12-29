# Generated by Django 3.1.4 on 2020-12-27 16:26

import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
from django.conf import settings
from django.db import migrations, models

import trips.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="Trip",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="modified"
                    ),
                ),
                ("name", models.CharField(max_length=1024)),
                ("description", models.TextField(max_length=102400, null=True)),
                ("cover_image", models.ImageField(null=True, upload_to=trips.models.upload_to)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                (
                    "polymorphic_ctype",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="polymorphic_trips.trip_set+",
                        to="contenttypes.contenttype",
                    ),
                ),
            ],
            options={"abstract": False, "base_manager_name": "objects",},
        ),
        migrations.CreateModel(
            name="CycleTrip",
            fields=[
                (
                    "trip_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="trips.trip",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[("R", "Road"), ("T", "Touring"), ("M", "Mountain"), ("G", "Gravel")],
                        db_index=True,
                        max_length=1,
                    ),
                ),
            ],
            options={"abstract": False, "base_manager_name": "objects",},
            bases=("trips.trip",),
        ),
    ]
