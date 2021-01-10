import graphql_jwt
from django.shortcuts import get_object_or_404
from graphene import ID, Field, Int, List, Mutation, ObjectType, String
from graphene_django.types import DjangoObjectType
from graphql import GraphQLError
from graphql_jwt.decorators import login_required

from .forms import EmailUserCreationForm
from .models import User


class UserPublicType(DjangoObjectType):
    class Meta:
        model = User
        fields = (
            "id",
            "name",
            "logbook_prefix",
            "logbook_title",
            "last_login",
            "date_joined",
        )


class UserPrivateType(DjangoObjectType):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "name",
            "logbook_prefix",
            "logbook_title",
            "logbook_header_image",
            "last_login",
            "date_joined",
        )


class Logbook(ObjectType):
    prefix = String()
    title = String()
    tracks = List("tours.schema.TrackType")  # avoid circular import


class Query:
    user = Field(UserPublicType, id=Int(required=True))
    me = Field(UserPrivateType)
    logbook = Field(Logbook, prefix=ID(required=True))

    @staticmethod
    def resolve_user(self, info, **kwargs):
        return User.objects.get(**kwargs)

    @staticmethod
    @login_required
    def resolve_me(self, info):
        return info.context.user

    @staticmethod
    def resolve_logbook(self, info, **kwargs):
        user = get_object_or_404(User, logbook_prefix=kwargs["prefix"])
        return Logbook(prefix=user.logbook_prefix, title=user.logbook_title, tracks=user.track_set.all())


class CreateUser(Mutation):
    id = ID()
    email = String()
    name = String()

    class Arguments:
        email = String(required=True)
        password = String(required=True)
        name = String(required=True)

    @staticmethod
    def mutate(self, info, **kwargs):
        kwargs["password1"] = kwargs["password2"] = kwargs["password"]
        form = EmailUserCreationForm(data=kwargs)
        if not form.is_valid():
            raise GraphQLError(list(dict(form.errors).values())[0][0])
        form.save()


class Mutation(ObjectType):
    user_create = CreateUser.Field()
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    token_verify = graphql_jwt.Verify.Field()
    token_refresh = graphql_jwt.Refresh.Field()
