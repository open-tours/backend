# Generated by Django 3.1.5 on 2021-01-12 17:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0006_user_logbook_header_image"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="logbook_prefix",
            field=models.CharField(blank=True, max_length=25, null=True, unique=True),
        ),
    ]
