from django.core.management.base import BaseCommand

from apps.alerts.services import AlertService


class Command(BaseCommand):
    help = "Corre los analyzers y crea/actualiza alertas pendientes (idempotente)"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true",
                            help="Muestra lo que se crearía sin escribir")

    def handle(self, *args, **options):
        candidatos = AlertService.build_alerts()
        creadas = actualizadas = 0
        if options["dry_run"]:
            self.stdout.write(f"dry-run: {len(candidatos)} alertas candidatas")
            return

        for candidato in candidatos:
            _, creada = AlertService.upsert_from_analysis(**candidato)
            creadas += bool(creada)
            actualizadas += not creada

        self.stdout.write(
            f"generar_alertas: {creadas} creadas, {actualizadas} actualizadas, "
            f"{len(candidatos)} candidatos"
        )