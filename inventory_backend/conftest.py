import pytest
from django.apps import apps
from django.db.models.signals import pre_migrate

SCHEMAS = ["inventory_agent", "production", "sales", "purchasing", "person", "humanresources"]

# Los modelos de AdventureWorks son unmanaged (managed=False) porque las tablas ya existen.
# Durante los tests necesitamos que run_syncdb las cree en la BD de pruebas, por eso se
# marking gestionados a nivel de import (antes de que pytest-django arme la BD de test).
_AW_MODELS = [m for m in apps.get_models() if not m._meta.managed]
for _model in _AW_MODELS:
    _model._meta.managed = True


def _create_schemas(sender, using, **kwargs):
    from django.db import connections
    with connections[using].cursor() as c:
        for s in SCHEMAS:
            c.execute(f'CREATE SCHEMA IF NOT EXISTS "{s}"')


pre_migrate.connect(_create_schemas, weak=False, dispatch_uid="create_aw_schemas")


@pytest.fixture
def api(db):
    from django.contrib.auth.models import Group, User
    from rest_framework.test import APIClient

    user = User.objects.create_user("tester", password="x")
    for role in ("viewer", "analyst", "inventory_manager"):
        Group.objects.get_or_create(name=role)[0]
    client = APIClient()
    client.force_authenticate(user)
    client.user = user
    return client
