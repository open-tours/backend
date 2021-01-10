import os
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from easy_thumbnails.files import get_thumbnailer
from exif import Image
from model_utils.models import TimeStampedModel
from polymorphic.models import PolymorphicModel

from .utils.geo import degrees_minutes_seconds_to_decimal


def upload_to(instance, filename):
    ext = os.path.splitext(filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    today_path = timezone.now().strftime("%Y/%m/%d")
    return os.path.join(f"uploads/tours/{today_path}", filename)


class Tour(PolymorphicModel, TimeStampedModel):
    name = models.CharField(max_length=1024, blank=False, null=False)
    start_date = models.DateField(blank=False, null=False)
    end_date = models.DateField(blank=False, null=False)
    description = models.TextField(max_length=102400, blank=False, null=True)
    cover_image = models.ImageField(upload_to=upload_to, blank=False, null=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,)

    class Meta:
        ordering = ["-id"]

    def get_cover_image_preview_url(self, request):
        if not self.cover_image.name:
            return None
        thumbnailer = get_thumbnailer(self.cover_image)
        image_url_path = thumbnailer["preview"].url
        return request.build_absolute_uri(image_url_path)


class CyclingTour(Tour):
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


class Track(PolymorphicModel, TimeStampedModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, blank=False, null=False)
    name = models.CharField(max_length=1024, blank=False, null=False)
    description = models.TextField(max_length=102400, blank=False, null=True)
    tour = models.ForeignKey(Tour, blank=False, null=True, on_delete=models.PROTECT,)
    gpx_file = models.FileField(upload_to=upload_to, blank=False, null=True)
    geojson = models.FileField(upload_to=upload_to, blank=False, null=True)
    start_date = models.DateField(blank=False, null=False)
    end_date = models.DateField(blank=False, null=False)
    moving_time_s = models.IntegerField(blank=False, null=True)
    stopped_time_s = models.IntegerField(blank=False, null=True)
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=True)
    uphill_m = models.DecimalField(max_digits=10, decimal_places=1, blank=False, null=True)
    downhill_m = models.DecimalField(max_digits=10, decimal_places=1, blank=False, null=True)
    max_speed_km_per_h = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=True)
    avg_speed_km_per_h = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=True)

    class Meta:
        ordering = ["start_date"]

    def get_geojson_url(self, request):
        if self.geojson.name:
            return request.build_absolute_uri(self.geojson.url)


class TrackPhoto(models.Model):
    track = models.ForeignKey(Track, blank=False, null=False, on_delete=models.CASCADE)
    file = models.ImageField(upload_to=upload_to, blank=False, null=False)
    longitude = models.DecimalField(max_digits=8, decimal_places=5, blank=False, null=True)
    latitude = models.DecimalField(max_digits=8, decimal_places=5, blank=False, null=True)

    def get_url(self, request):
        return request.build_absolute_uri(self.file.url)

    def get_preview_url(self, request):
        thumbnailer = get_thumbnailer(self.file)
        image_url_path = thumbnailer["preview"].url
        return request.build_absolute_uri(image_url_path)

    def get_icon_url(self, request):
        thumbnailer = get_thumbnailer(self.file)
        image_url_path = thumbnailer["icon"].url
        return request.build_absolute_uri(image_url_path)

    def save(self, *args, **kwargs):
        # save lat / long
        exif_data = Image(self.file.read())
        if hasattr(exif_data, "gps_longitude") and hasattr(exif_data, "gps_latitude"):
            self.longitude = degrees_minutes_seconds_to_decimal(*exif_data.gps_longitude)
            self.latitude = degrees_minutes_seconds_to_decimal(*exif_data.gps_latitude)
        super().save(*args, **kwargs)


class CyclingTrack(Track):
    pass
