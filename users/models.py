import os
import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from easy_thumbnails.files import get_thumbnailer

from .managers import UserManager


def upload_to(instance, filename):
    ext = os.path.splitext(filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    today_path = timezone.now().strftime("%Y/%m/%d")
    return os.path.join(f"uploads/users/{today_path}", filename)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    date_joined = models.DateTimeField(default=timezone.now)
    profile_image = models.ImageField(upload_to=upload_to, blank=True, null=True)
    logbook_prefix = models.CharField(max_length=15, blank=True, null=True, unique=True)
    logbook_title = models.TextField(max_length=250, blank=True, null=True)
    logbook_header_image = models.ImageField(upload_to=upload_to, blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def is_staff(self):
        return self.is_superuser

    def get_profile_image_url(self, request):
        thumbnailer = get_thumbnailer(self.profile_image)
        image_url_path = thumbnailer["small"].url
        return request.build_absolute_uri(image_url_path)

    def get_logbook_header_image_url(self, request):
        thumbnailer = get_thumbnailer(self.logbook_header_image)
        image_url_path = thumbnailer["scaled"].url
        return request.build_absolute_uri(image_url_path)
