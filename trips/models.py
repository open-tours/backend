import os
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from easy_thumbnails.files import get_thumbnailer
from model_utils.models import TimeStampedModel
from polymorphic.models import PolymorphicModel


def upload_to(instance, filename):
    ext = os.path.splitext(filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    today_path = timezone.now().strftime("%Y/%m/%d")
    return os.path.join(f"uploads/trips/{today_path}", filename)


class Trip(PolymorphicModel, TimeStampedModel):
    name = models.CharField(max_length=1024, blank=False, null=False)
    start_date = models.DateField(blank=False, null=False)
    end_date = models.DateField(blank=False, null=False)
    description = models.TextField(max_length=102400, blank=True, null=True)
    cover_image = models.ImageField(upload_to=upload_to, blank=True, null=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,)

    class Meta:
        ordering = ["-id"]

    def get_cover_image_preview_abs_url(self, request):
        if not self.cover_image.name:
            return None
        thumbnailer = get_thumbnailer(self.cover_image)
        image_url_path = thumbnailer["preview"].url
        return request.build_absolute_uri(image_url_path)


class CyclingTrip(Trip):
    TYPE_ROAD = "R"
    TYPE_TOURING = "T"
    TYPE_MOUNTAIN = "M"
    TYPE_GRAVEL = "G"
    TYPE_CHOICES = [
        (TYPE_ROAD, _("Road")),
        (TYPE_TOURING, _("Touring")),
        (TYPE_MOUNTAIN, _("Mountain")),
        (TYPE_GRAVEL, _("Gravel")),
    ]
    type = models.CharField(max_length=1, choices=TYPE_CHOICES, blank=False, null=False, db_index=True)


class Stage(PolymorphicModel, TimeStampedModel):
    trip = models.ForeignKey(Trip, blank=False, null=False, on_delete=models.PROTECT,)
    gpx_file = models.FileField(upload_to=upload_to, blank=True, null=True)
    start_date = models.DateField(blank=False, null=False)
    end_date = models.DateField(blank=False, null=False)
    moving_time_s = models.IntegerField(blank=True, null=True)
    stopped_time_s = models.IntegerField(blank=True, null=True)
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    uphill_m = models.DecimalField(max_digits=10, decimal_places=1, blank=True, null=True)
    downhill_m = models.DecimalField(max_digits=10, decimal_places=1, blank=True, null=True)
    max_speed_km_per_h = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    avg_speed_km_per_h = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)


class CyclingStage(Stage):
    pass
