# Generated by Django 3.1.4 on 2021-01-03 13:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("tours", "0002_auto_20210103_1338"),
    ]

    operations = [
        migrations.RemoveField(model_name="stage", name="gpx",),
    ]
