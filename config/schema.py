import graphene

import tours.schema
import users.schema


class Query(users.schema.Query, tours.schema.Query, graphene.ObjectType):
    pass


class Mutation(users.schema.Mutation, tours.schema.Mutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
