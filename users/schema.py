import graphql_jwt
from graphene import ID, Field, Int, Mutation, ObjectType, String
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
            "last_login",
            "date_joined",
        )


class Query:
    user = Field(UserPublicType, id=Int(required=True))
    me = Field(UserPrivateType)

    @staticmethod
    def resolve_user(self, info, **kwargs):
        return User.objects.get(**kwargs)

    @staticmethod
    @login_required
    def resolve_me(self, info):
        return info.context.user


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
