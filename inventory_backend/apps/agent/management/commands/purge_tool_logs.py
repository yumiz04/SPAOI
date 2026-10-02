from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.agent.models import ToolLog


class Command(BaseCommand):
    """Politica de retencion de la traza del agente (SRS §27-§28)."""

    help = "Elimina las trazas de agent_tool_log anteriores al periodo de retencion."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days", type=int, default=None,
            help="Antiguedad en dias (por defecto AGENT_TOOL_LOG_RETENTION_DAYS).",
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Solo informa cuantas trazas se borrarian.",
        )

    def handle(self, *args, **options):
        days = options["days"] or getattr(settings, "AGENT_TOOL_LOG_RETENTION_DAYS", 180)
        corte = timezone.now() - timedelta(days=days)
        qs = ToolLog.objects.filter(timestamp__lt=corte)
        total = qs.count()

        if options["dry_run"]:
            self.stdout.write(
                f"[dry-run] se borrarian {total} trazas anteriores a {corte:%Y-%m-%d}"
            )
            return

        borradas, _ = qs.delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"{borradas} trazas eliminadas (retencion de {days} dias)"
            )
        )
