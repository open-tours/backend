# Generated by Django 3.1.4 on 2020-12-29 20:37

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("trips", "0004_cyclestage_stage"),
    ]

    operations = [
        migrations.RenameModel(old_name="CycleTrip", new_name="CyclingTrip",),
    ]
