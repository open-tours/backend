import math
from io import StringIO

import gpxpy
from django.contrib.gis.geos import LineString, Point
from django.core.files import File
from django.db.transaction import atomic
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from gpxpy.gpx import GPXXMLSyntaxException
from graphene import Argument, Date, Field, Float, InputObjectType, Int, List, Mutation, ObjectType, String
from graphene_django.types import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql import GraphQLError
from graphql_jwt.decorators import login_required

from users.schema import UserPublicType
from utils.graphene import field_name_to_readable

from .models import CyclingStage, CyclingTour


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
    cover_image = Field(String)

    @staticmethod
    def resolve_cover_image(self, info):
        return self.get_cover_image_preview_abs_url(info.context)


class HoursMinutesType(ObjectType):
    hours = Int()
    minutes = Int()


class HoursMinutesArgument(InputObjectType):
    hours = Int()
    minutes = Int()


class StageTypeMixin:
    name = String()
    start_date = Date()
    end_date = Date()
    distance_km = Float()
    moving_time = Field(HoursMinutesType)
    stopped_time = Field(HoursMinutesType)
    max_speed_km_per_h = Float()
    avg_speed_km_per_h = Float()
    uphill_m = Float()
    downhill_m = Float()


class CreateStage(StageTypeMixin, Mutation):
    class Arguments:
        gpx_file = Upload()
        name = String(required=True)
        tour_id = Int(required=True)
        start_date = Date(required=True)
        end_date = Date(required=True)
        distance_km = Float()
        moving_time = Argument(HoursMinutesArgument)
        stopped_time = Argument(HoursMinutesArgument)
        max_speed_km_per_h = Float()
        avg_speed_km_per_h = Float()
        uphill_m = Float()
        downhill_m = Float()

    @staticmethod
    @login_required
    @atomic
    def mutate(self, info, **fields):
        # validate moving_time and stopped_time
        for field in ["moving_time", "stopped_time"]:
            if field not in fields:
                continue

            # validate
            if "minutes" in fields[field]:
                if fields[field]["minutes"] < 0 or fields[field]["minutes"] > 59:
                    raise GraphQLError(_(f"Minutes not in range 0-59 for {field_name_to_readable(field)}"))

            if fields[field]["hours"] < 0:
                raise GraphQLError(_(f"Hours can not be negative for {field_name_to_readable(field)}"))

            # to seconds
            fields[f"{field}_s"] = fields[field]["hours"] * 3600 + fields[field]["minutes"] * 60
            del fields[field]

        # force positive int/float values
        for field, value in fields.items():
            if not isinstance(value, (float, int)):
                continue
            value = float(value)
            if value < 0:
                raise GraphQLError(_(f"Value can not be negative for {field_name_to_readable(field)}"))

        # create object
        get_object_or_404(CyclingTour, pk=fields.get("tour_id"), owner=info.context.user)
        stage = CyclingStage(**fields)

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
            tolerance = 0.001
            line_string = LineString([Point(p.point.longitude, p.point.latitude).coords for p in gpx.get_points_data()])
            line_string = line_string.simplify(tolerance, True)

            # save gpx file
            stage.geojson_preview.save(f"{stage.pk}.json", File(StringIO(line_string.geojson)))

        stage.save()


class GPXFileInfoUpload(StageTypeMixin, Mutation):
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

        gpx_info = {
            "name": gpx.tracks[0].name or "" + " " + gpx.tracks[0].description or "",
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


class Query:
    tours = List(TourType)
    tour = Field(TourType, id=Int(required=True))
    my_tours = List(TourType)

    @staticmethod
    def resolve_tours(self, info, **kwargs):
        return CyclingTour.objects.all()

    @staticmethod
    def resolve_tour(self, info, **kwargs):
        return get_object_or_404(CyclingTour, owner=info.context.user, **kwargs)

    @login_required
    def resolve_my_tours(self, info):
        return CyclingTour.objects.filter(owner=info.context.user)


class Mutation(ObjectType):
    gpx_file_info = GPXFileInfoUpload.Field()
    stageCreate = CreateStage().Field()
