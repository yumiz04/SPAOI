from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.agent.models import ToolLog


def _log(request_id):
    return ToolLog.objects.create(
        request_id=request_id, tool="obtener_existencias",
        parameters={}, execution_time_ms=1.0, success=True,
    )


@pytest.mark.django_db
def test_purge_tool_logs_borra_las_antiguas():
    viejo = _log("viejo")
    ToolLog.objects.filter(pk=viejo.pk).update(
        timestamp=timezone.now() - timedelta(days=400)
    )
    nuevo = _log("nuevo")

    call_command("purge_tool_logs", days=180)

    assert not ToolLog.objects.filter(pk=viejo.pk).exists()
    assert ToolLog.objects.filter(pk=nuevo.pk).exists()


@pytest.mark.django_db
def test_purge_tool_logs_dry_run_no_borra():
    _log("uno")

    call_command("purge_tool_logs", days=0, dry_run=True)

    assert ToolLog.objects.count() == 1
