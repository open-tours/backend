from django.utils.timezone import now
from graphql_jwt.signals import token_issued


def update_last_login(**kwargs):
    kwargs["user"].last_login = now()
    kwargs["user"].save()


token_issued.connect(update_last_login)
