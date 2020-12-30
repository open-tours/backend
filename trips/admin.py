from django.contrib import admin

from .models import CyclingTrip


@admin.register(CyclingTrip)
class CyclingTripAdmin(admin.ModelAdmin):
    pass
