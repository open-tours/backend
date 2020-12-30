import math

import gpxpy
from django.utils.translation import gettext_lazy as _
from gpxpy.gpx import GPXXMLSyntaxException
from graphene import Field, Float, Int, List, Mutation, ObjectType, String
from graphene_django.types import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql import GraphQLError
from graphql_jwt.decorators import login_required

from users.schema import UserPublicType

from .models import CyclingTrip


class TripType(DjangoObjectType):
    class Meta:
        model = CyclingTrip
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


class GPXFileInfoUpload(Mutation):
    name = String()
    start_date = String()
    end_date = String()
    distance_km = Float()
    moving_time = Field(HoursMinutesType)
    stopped_time = Field(HoursMinutesType)
    max_speed_km_per_h = Float()
    avg_speed_km_per_h = Float()
    uphill_m = Float()
    downhill_m = Float()

    class Arguments:
        file = Upload(required=True)

    @login_required
    def mutate(self, info, **kwargs):
        gpx_file = kwargs["file"]
        try:
            gpx = gpxpy.parse(gpx_file.file.read())

            if len(gpx.tracks) == 0:
                raise GraphQLError(_("No Tracks found in your GPX file."))
            if len(gpx.tracks) > 1:
                raise GraphQLError(_("Only one Track in a GPX file is allowed."))

            if len(gpx.tracks[0].segments) == 0:
                raise GraphQLError(_("No Track Segments found in your GPX file."))
            if len(gpx.tracks[0].segments) > 1:
                raise GraphQLError(_("Only one Segment per Track in a GPX file is allowed."))

            segment = gpx.tracks[0].segments[0]
            uphill, downhill = segment.get_uphill_downhill()

            gpx_info = {
                "name": gpx.name or "",
                "distance_km": round((segment.length_2d() or 0) / 1000, 2) or None,
                "uphill_m": round(uphill or 0, 2) or None,
                "downhill_m": round(downhill or 0, 2) or None,
            }

            # start end time
            start_time, end_time = segment.get_time_bounds()
            if start_time:
                gpx_info["start_date"] = start_time.date()
            if end_time:
                gpx_info["end_date"] = end_time.date()

            moving_data = segment.get_moving_data()
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
        except (GPXXMLSyntaxException, UnicodeDecodeError):
            raise GraphQLError(_("GPX format is unknown."))


class Query:
    trips = List(TripType)
    trip = Field(TripType, id=Int(required=True))
    my_trips = List(TripType)

    @staticmethod
    def resolve_trips(self, info, **kwargs):
        return CyclingTrip.objects.all()

    @staticmethod
    def resolve_trip(self, info, **kwargs):
        return CyclingTrip.objects.get(**kwargs)

    @staticmethod
    @login_required
    def resolve_my_trips(self, info):
        return CyclingTrip.objects.filter(owner=info.context.user)


class Mutation(ObjectType):
    gpx_file_info = GPXFileInfoUpload.Field()
