from django.contrib import admin

from .models import CyclingTour


@admin.register(CyclingTour)
class CyclingTrackAdmin(admin.ModelAdmin):
    pass
