import os

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError

ROLES = ["viewer", "analyst", "inventory_manager"]


class Command(BaseCommand):
    help = "Crea/actualiza el superusuario desde DJANGO_SUPERUSER_* (idempotente)."

    def handle(self, *args, **opts):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")

        if not password:
            raise CommandError(
                "Define DJANGO_SUPERUSER_PASSWORD para crear el superusuario."
            )

        user, created = User.objects.get_or_create(
            username=username, defaults={"email": email}
        )
        user.email = email or user.email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()
        user.groups.set(Group.objects.filter(name__in=ROLES))

        self.stdout.write(
            f"Superusuario '{username}' {'creado' if created else 'actualizado'}"
        )
