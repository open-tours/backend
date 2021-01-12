import re

import graphql_jwt
from django.conf import settings as s
from django.db.models import FileField, ImageField
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from graphene import ID, Field, Int, List, Mutation, ObjectType, String
from graphene_django.types import DjangoObjectType
from graphene_file_upload.scalars import Upload
from graphql import GraphQLError
from graphql_jwt.decorators import login_required

from .forms import EmailUserCreationForm
from .models import User


class UserTypeBase:
    def resolve_profile_image(self, info):
        return self.get_profile_image_url(info.context)

    def resolve_logbook_header_image(self, info):
        return self.get_logbook_header_image_url(info.context)


class UserPublicType(UserTypeBase, DjangoObjectType):
    class Meta:
        model = User
        fields = (
            "id",
            "name",
            "profile_image",
            "logbook_subdomain",
            "logbook_title",
            "logbook_header_image",
            "last_login",
            "date_joined",
        )


class UserPrivateType(UserTypeBase, DjangoObjectType):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "name",
            "profile_image",
            "logbook_subdomain",
            "logbook_title",
            "logbook_header_image",
            "last_login",
            "date_joined",
        )


class Logbook(ObjectType):
    subdomain = String()
    title = String()
    header_image = Upload()
    tracks = List("tours.schema.TrackType")  # avoid circular import


class Query:
    user = Field(UserPublicType, id=Int(required=True))
    me = Field(UserPrivateType)
    logbook = Field(Logbook, subdomain=ID(required=True))

    @staticmethod
    def resolve_user(self, info, **kwargs):
        return User.objects.get(**kwargs)

    @staticmethod
    @login_required
    def resolve_me(self, info):
        return info.context.user

    @staticmethod
    def resolve_logbook(self, info, **kwargs):
        user = get_object_or_404(User, logbook_subdomain=kwargs["subdomain"])
        return Logbook(
            subdomain=user.logbook_subdomain,
            title=user.logbook_title,
            header_image=user.get_logbook_header_image_url(info.context),
            tracks=user.track_set.all(),
        )


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


class UpdateUser(Mutation):
    id = ID()

    class Arguments:
        name = String()
        profile_image = Upload()
        logbook_title = String()
        logbook_subdomain = String()
        logbook_header_image = Upload()

    @staticmethod
    @login_required
    def mutate(self, info, **fields):
        user = info.context.user
        for field, value in fields.items():
            # file size and type check
            model_field = User._meta.get_field(field)
            if isinstance(model_field, FileField):
                if value.size > s.IMAGE_MAX_FILESIZE_BYTES:
                    raise GraphQLError(_("Image file size too large"))
            if isinstance(model_field, ImageField):
                if value.content_type not in s.IMAGE_ALLOWED_CONTENT_TYPES:
                    raise GraphQLError(_("Invalid image type"))

            if field == "logbook_subdomain":
                if value:
                    value = value.lower()
                    if not re.match("^[a-z0-9_-]+$", value):
                        raise GraphQLError(_("A subdomain can only contain characters a-z, 0-9, - and _"))
                    if value in ["www", "webmail", "mail", "prod", "stage", "test", "example"]:
                        raise GraphQLError(_("This subdomain is not allowed"))
                    if User.objects.filter(logbook_subdomain=value).exists():
                        raise GraphQLError(_("Subdomain already exists"))

            setattr(user, field, value)
        user.save()


class Mutation(ObjectType):
    user_create = CreateUser.Field()
    user_update = UpdateUser.Field()
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    token_verify = graphql_jwt.Verify.Field()
    token_refresh = graphql_jwt.Refresh.Field()
