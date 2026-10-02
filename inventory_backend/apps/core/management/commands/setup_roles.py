from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

ROLES = ["viewer", "analyst", "inventory_manager"]

class Command(BaseCommand):
    def handle(self, *args, **opts):
        for r in ROLES:
            Group.objects.get_or_create(name=r)
        self.stdout.write("Roles listos")