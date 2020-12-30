import graphene

import trips.schema
import users.schema


class Query(users.schema.Query, trips.schema.Query, graphene.ObjectType):
    pass


class Mutation(users.schema.Mutation, trips.schema.Mutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
