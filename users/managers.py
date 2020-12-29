from django.contrib.auth.base_user import BaseUserManager
from django.db import IntegrityError
from django.utils.translation import ugettext_lazy as _


class UserManager(BaseUserManager):
    def create(self, email, password, **fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **fields)
        user.set_password(password)
        user.save()
        return user

    def create_user(self, email, password, **fields):
        if not email:
            raise ValueError(_("The Email must be set"))
        if fields.get("is_superuser") is True:
            raise ValueError(_("Normal user cannot be a super user."))
        try:
            return self.create(email, password, **fields)
        except IntegrityError:
            raise ValueError(
                _(
                    "An account with this email address already exists. Log in with your existing data or reset your password."
                )
            )

    def create_superuser(self, email, password, **fields):
        fields.setdefault("is_superuser", True)

        if fields.get("is_superuser") is not True:
            raise ValueError(_("Super user must have super_user set to True"))
        return self.create(email, password, **fields)
