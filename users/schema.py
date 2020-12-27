import graphql_jwt
from graphene import ID, Field, Int, Mutation, ObjectType, String
from graphene_django.types import DjangoObjectType
from graphql_jwt.decorators import login_required

from .models import User


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "last_login",
            "date_joined",
        )


class Query(object):
    user = Field(UserType, id=Int())
    me = Field(UserType)

    @staticmethod
    def resolve_user(self, info, **kwargs):
        return User.objects.get_by_id(**kwargs)

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
    def mutate(cls, info, email, password, name):
        user = User.objects.create_user(email=email, password=password, name=name)
        return CreateUser(id=user.id, email=user.email, name=name)


class Mutation(ObjectType):
    user_create = CreateUser.Field()
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    token_verify = graphql_jwt.Verify.Field()
    token_refresh = graphql_jwt.Refresh.Field()
