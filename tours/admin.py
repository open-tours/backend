from django.contrib import admin

from .models import CyclingTour


@admin.register(CyclingTour)
class CyclingTripAdmin(admin.ModelAdmin):
    pass
