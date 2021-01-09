import math
from io import StringIO

import gpxpy
from django.conf import settings as s
from django.contrib.gis.geos import LineString, Point
from django.core.files import File
from django.db.transaction import atomic
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from gpxpy.gpx import GPXXMLSyntaxException
from graphene import ID, Argument, Date, Field, Float, InputObjectType, Int, List, Mutation, ObjectType, String
from graphene_django.types import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql import GraphQLError
from graphql_jwt.decorators import login_required

from users.schema import UserPublicType
from utils.graphene import field_name_to_readable

from .models import CyclingTour, CyclingTrack, TrackPhoto


class HoursMinutesType(ObjectType):
    hours = Int()
    minutes = Int()


class HoursMinutesArgument(InputObjectType):
    hours = Int()
    minutes = Int()


class PhotoType(ObjectType):
    url = String()
    icon_url = String()
    preview_url = String()
    longitude = Float()
    latitude = Float()


class TrackTypeMixin:
    id = ID()
    name = String()
    owner = Field(UserPublicType)
    description = String()
    start_date = Date()
    end_date = Date()
    distance_km = Float()
    moving_time = Field(HoursMinutesType)
    stopped_time = Field(HoursMinutesType)
    max_speed_km_per_h = Float()
    avg_speed_km_per_h = Float()
    uphill_m = Float()
    downhill_m = Float()
    photos = List(Upload)


class TrackType(TrackTypeMixin, DjangoObjectType):
    class Meta:
        model = CyclingTrack
        fields = (
            "id",
            "name",
            "owner",
            "description",
            "start_date",
            "end_date",
            "created",
        )

    geojson = String()
    photos = List(PhotoType)

    @staticmethod
    def resolve_moving_time(self, info):
        if self.moving_time_s:
            minutes = math.floor(self.moving_time_s / 60)
            hours = math.floor(minutes / 60)
            return HoursMinutesType(hours=hours, minutes=minutes % 60)

    @staticmethod
    def resolve_stopped_time(self, info):
        if self.stopped_time_s:
            minutes = math.floor(self.stopped_time_s / 60)
            hours = math.floor(minutes / 60)
            return HoursMinutesType(hours=hours, minutes=minutes % 60)

    @staticmethod
    def resolve_geojson(self, info):
        return self.get_geojson_url(info.context)

    @staticmethod
    def resolve_photos(self, info):
        photos = []
        for photo in self.trackphoto_set.all():
            photos.append(
                PhotoType(
                    url=photo.get_url(info.context),
                    preview_url=photo.get_preview_url(info.context),
                    icon_url=photo.get_icon_url(info.context),
                    longitude=photo.longitude,
                    latitude=photo.latitude,
                )
            )
        return photos


class CreateTrack(TrackTypeMixin, Mutation):
    class Arguments:
        name = String(required=True)
        description = String()
        tour_id = ID()
        gpx_file = Upload()
        start_date = Date(required=True)
        end_date = Date(required=True)
        distance_km = Float()
        moving_time = Argument(HoursMinutesArgument)
        stopped_time = Argument(HoursMinutesArgument)
        max_speed_km_per_h = Float()
        avg_speed_km_per_h = Float()
        uphill_m = Float()
        downhill_m = Float()
        photos = List(Upload)

    @staticmethod
    @login_required
    @atomic
    def mutate(self, info, **fields):
        # validate moving_time and stopped_time
        for field in ["moving_time", "stopped_time"]:
            if field not in fields:
                continue

            # validate
            if (fields[field].get("hours") or 0) < 0:
                raise GraphQLError(_(f"Hours can not be negative for {field_name_to_readable(field)}"))
            if fields[field].get("minutes"):
                if fields[field]["minutes"] < 0 or fields[field]["minutes"] > 59:
                    raise GraphQLError(_(f"Minutes not in range 0-59 for {field_name_to_readable(field)}"))

            # to seconds
            if fields[field]["hours"] or fields[field]["minutes"]:
                fields[f"{field}_s"] = (fields[field]["hours"] or 0) * 3600 + (fields[field]["minutes"] or 0) * 60
            del fields[field]

        # force positive int/float values
        for field, value in fields.items():
            if not isinstance(value, (float, int)):
                continue
            value = float(value)
            if value < 0:
                raise GraphQLError(_(f"Value can not be negative for {field_name_to_readable(field)}"))

        # validate tour
        tour_id = fields.get("tour_id")
        if tour_id:
            get_object_or_404(CyclingTour, pk=tour_id, owner=info.context.user)

        # create track
        photos = fields.get("photos", []) or []
        if "photos" in fields:
            del fields["photos"]

        # validate images
        for photo in photos:
            if photo.content_type not in s.IMAGE_ALLOWED_CONTENT_TYPES:
                raise GraphQLError(_("Invalid image type"))
            if photo.size > s.IMAGE_MAX_FILESIZE_BYTES:
                raise GraphQLError(_("Image file size too large"))

        track = CyclingTrack(owner=info.context.user, **fields)

        # append gpx file
        gpx_file = fields.get("gpx_file")
        if gpx_file:
            try:
                gpx = gpxpy.parse(gpx_file.file.read())
                gpx.smooth(vertical=True, horizontal=False, remove_extremes=False)
                gpx_file.seek(0)
            except (GPXXMLSyntaxException, UnicodeDecodeError) as e:
                print(e)
                raise GraphQLError(_("GPX format is unknown."))

            # save geojson preview
            tolerance = 0.0001
            line_string = LineString([Point(p.point.longitude, p.point.latitude).coords for p in gpx.get_points_data()])
            line_string = line_string.simplify(tolerance, True)

            # save gpx file
            track.geojson.save(f"{track.pk}.json", File(StringIO(line_string.geojson)))

        track.save()

        # add images
        for photo in photos:
            TrackPhoto.objects.create(
                track=track, file=photo,
            )


class GPXFileInfoUpload(TrackTypeMixin, Mutation):
    class Arguments:
        file = Upload(required=True)

    @staticmethod
    @login_required
    def mutate(self, info, **fields):
        gpx_file = fields["file"]

        try:
            gpx = gpxpy.parse(gpx_file.file.read())
            gpx.smooth(vertical=True, horizontal=False, remove_extremes=False)
        except (GPXXMLSyntaxException, UnicodeDecodeError):
            raise GraphQLError(_("GPX format is unknown."))

        if len(gpx.tracks) == 0:
            raise GraphQLError(_("No Tracks found in your GPX file."))

        uphill, downhill = gpx.get_uphill_downhill()

        # construct name from track / gpx metadata
        name = ""
        if gpx.name:
            name = gpx.name
        if gpx.description:
            name += f" {gpx.description}"
        if gpx.tracks[0].name and gpx.tracks[0].name not in name:
            name += gpx.tracks[0].name
        if gpx.tracks[0].description and gpx.tracks[0].description not in name:
            name += f" {gpx.tracks[0].description}"
        if not name:
            name = None

        gpx_info = {
            "name": name,
            "distance_km": round((gpx.length_2d() or 0) / 1000, 2) or None,
            "uphill_m": round(uphill or 0, 2) or None,
            "downhill_m": round(downhill or 0, 2) or None,
        }

        # start end time
        start_time, end_time = gpx.get_time_bounds()
        if start_time:
            gpx_info["start_date"] = start_time.date()
        if end_time:
            gpx_info["end_date"] = end_time.date()

        moving_data = gpx.get_moving_data(speed_extreemes_percentiles=0.015)
        if moving_data:
            # moving time
            moving_time_minutes = math.floor(moving_data.moving_time / 60)
            moving_time_hours = math.floor(moving_time_minutes / 60)
            gpx_info["moving_time"] = HoursMinutesType(hours=moving_time_hours, minutes=moving_time_minutes % 60)

            # stopped time
            stopped_time_minutes = math.floor(moving_data.stopped_time / 60)
            stopped_time_hours = math.floor(stopped_time_minutes / 60)
            gpx_info["stopped_time"] = HoursMinutesType(hours=stopped_time_hours, minutes=stopped_time_minutes % 60)

            # max speed
            gpx_info["max_speed_km_per_h"] = round(moving_data.max_speed * 3600 / 1000, 2) or None

            # avg speed
            avg_speed = 0
            if moving_data.moving_time > 0:
                avg_speed = moving_data.moving_distance / moving_data.moving_time
            gpx_info["avg_speed_km_per_h"] = round(avg_speed * 3600 / 1000, 2) or None

        return GPXFileInfoUpload(**gpx_info)


class TourType(DjangoObjectType):
    class Meta:
        model = CyclingTour
        fields = (
            "id",
            "name",
            "start_date",
            "end_date",
            "description",
            "owner",
            "created",
        )

    owner = Field(UserPublicType)
    tracks = List(TrackType)

    @staticmethod
    def resolve_track(self, info):
        return self.track_set.all()


class Query:
    tour = Field(TourType, id=ID(required=True))
    tours = List(TourType)
    track = Field(TrackType, id=ID(required=True))
    tracks = List(TrackType)
    my_tours = List(TourType)
    my_tracks = List(TrackType)

    @staticmethod
    def resolve_tour(self, info, **kwargs):
        return CyclingTour.objects.get(**kwargs)

    @staticmethod
    def resolve_tours(self, info, **kwargs):
        return CyclingTour.objects.all()

    @staticmethod
    def resolve_track(self, info, **kwargs):
        return CyclingTrack.objects.get(**kwargs)

    @staticmethod
    def resolve_tracks(self, info, **kwargs):
        return CyclingTrack.objects.all()

    @login_required
    def resolve_my_tours(self, info):
        return CyclingTour.objects.filter(owner=info.context.user)

    @login_required
    def resolve_my_tracks(self, info):
        return CyclingTrack.objects.filter(owner=info.context.user).order_by("-pk")


class Mutation(ObjectType):
    gpx_file_info = GPXFileInfoUpload.Field()
    track_create = CreateTrack().Field()
