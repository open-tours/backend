from graphene import Field, Int, List, String
from graphene_django.types import DjangoObjectType
from graphql_jwt.decorators import login_required

from users.schema import UserPublicType

from .models import Trip


class TripType(DjangoObjectType):
    class Meta:
        model = Trip
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


class Query(object):
    trips = List(TripType)
    trip = Field(TripType, id=Int(required=True))
    my_trips = List(TripType)

    @staticmethod
    def resolve_trips(self, info, **kwargs):
        return Trip.objects.all()

    @staticmethod
    def resolve_trip(self, info, **kwargs):
        return Trip.objects.get(**kwargs)

    @staticmethod
    @login_required
    def resolve_my_trips(self, info):
        return Trip.objects.filter(owner=info.context.user)
