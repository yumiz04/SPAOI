import datetime
import random

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.dates import as_of_date
from apps.inventory.models import ProductInventory
from apps.lots.models import Lot


class Command(BaseCommand):
    help = "Crea lotes para N productos con existencia, con caducidades repartidas."

    def add_arguments(self, parser):
        parser.add_argument("--products", type=int, default=25)
        parser.add_argument("--seed", type=int, default=20240101)

    @transaction.atomic
    def handle(self, *args, **opts):
        rng = random.Random(opts["seed"])
        hoy = as_of_date()

        stock = list(
            ProductInventory.objects.filter(quantity__gt=0)
            .values("product_id", "location_id", "quantity")
            .order_by("product_id", "location_id")[: opts["products"]]
        )
        if not stock:
            self.stdout.write(self.style.WARNING("No hay inventario para generar lotes"))
            return

        # Repartimos caducidades: ya vencidas, y a 10/30/90 días respecto a hoy.
        offsets = [-20, 10, 30, 90]
        creados = 0

        for fila in stock:
            total = fila["quantity"]
            n = rng.randint(1, 3)
            # Reparto entero cuya suma nunca excede la existencia (P4).
            cortes = sorted(rng.sample(range(1, total), n - 1)) if n > 1 else []
            partes = []
            previo = 0
            for c in cortes:
                partes.append(c - previo)
                previo = c
            partes.append(total - previo)

            for i, cantidad in enumerate(partes):
                offset = offsets[i % len(offsets)]
                caducidad = hoy + datetime.timedelta(days=offset)
                entrada = caducidad - datetime.timedelta(days=rng.randint(30, 180))
                if entrada > hoy:
                    entrada = hoy
                status = Lot.Status.CADUCADO if caducidad < hoy else Lot.Status.ACTIVO
                numero = f"SEED-{fila['product_id']}-{fila['location_id']}-{i + 1}"

                _, creado = Lot.objects.get_or_create(
                    product_id=fila["product_id"],
                    location_id=fila["location_id"],
                    lot_number=numero,
                    defaults={
                        "quantity": cantidad,
                        "entry_date": entrada,
                        "expiration_date": caducidad,
                        "status": status,
                    },
                )
                creados += int(creado)

        self.stdout.write(self.style.SUCCESS(f"Lotes creados: {creados}"))