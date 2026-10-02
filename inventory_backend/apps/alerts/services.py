from django.db import transaction

from apps.analytics import repositories as repo
from apps.analytics.analyzers.depletion import DepletionAnalyzer
from apps.analytics.analyzers.expiration import ExpirationAnalyzer
from apps.analytics.analyzers.overstock import OverstockAnalyzer
from apps.analytics.analyzers.stockout import StockoutAnalyzer
from apps.analytics.analyzers.turnover import TurnoverAnalyzer
from apps.core.dates import as_of_date
from apps.core.exceptions import AppError, NotFoundError
from apps.lots.models import Lot
from apps.products.models import Product
from apps.risk_config.services import RiskConfigService
from .models import Alert


class AlertService:
    """Alertas propias (inventory_agent.alertas). Paso 13 / RF-B15 / RN-B05."""

    @staticmethod
    def dedup_key(alert_type: str, product_id: int, location_id=None) -> str:
        return f"{alert_type}:{product_id}:{location_id or 0}"

    @staticmethod
    def create(product_id, alert_type, severity, message, details=None, location_id=None):
        """Alta manual (RF-B15)."""
        alerta = Alert(
            product_id=product_id,
            location_id=location_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            details=details or {},
            dedup_key=AlertService.dedup_key(alert_type, product_id, location_id),
        )
        try:
            with transaction.atomic():
                alerta.save()
        except Exception as exc:  # noqa: BLE001 - se traduce el error de unicidad
            if "uq_alerta_pendiente_dedup" in str(exc):
                raise AppError(
                    "DUPLICATE_ALERT",
                    "Ya existe una alerta pendiente de ese tipo para el producto y ubicación",
                    409,
                ) from exc
            raise
        return alerta

    @staticmethod
    def list(filters):
        """Lista filtrada: type, severity, status, product_id."""
        qs = Alert.objects.all()
        tipo = (filters or {}).get("type")
        if tipo:
            qs = qs.filter(alert_type=tipo)
        severidad = (filters or {}).get("severity")
        if severidad:
            qs = qs.filter(severity=severidad)
        estado = (filters or {}).get("status")
        if estado:
            qs = qs.filter(status=estado)
        producto = (filters or {}).get("product_id")
        if producto:
            qs = qs.filter(product_id=producto)
        return qs

    @staticmethod
    def update_status(alert_id: int, status: str, note: str | None = None) -> Alert:
        """Solo PENDIENTE -> ATENDIDA | DESCARTADA. Una alerta cerrada no se reabre."""
        if status not in (Alert.Status.ATENDIDA, Alert.Status.DESCARTADA):
            raise AppError(
                "INVALID_ALERT_STATUS",
                "Una alerta solo puede pasar a ATENDIDA o DESCARTADA",
                400,
            )
        with transaction.atomic():
            alerta = Alert.objects.select_for_update().filter(pk=alert_id).first()
            if alerta is None:
                raise NotFoundError("ALERT_NOT_FOUND", "Alerta no encontrada")
            if alerta.status != Alert.Status.PENDIENTE:
                raise AppError(
                    "ALERT_ALREADY_CLOSED",
                    f"La alerta ya está en estado {alerta.status} y no se puede modificar",
                    409,
                )
            alerta.status = status
            fields = ["status", "updated_at"]
            if note:
                alerta.details = dict(alerta.details or {}, resolution_note=note)
                fields.append("details")
            alerta.save(update_fields=fields)
        return alerta

    @staticmethod
    def to_dict(alerta: Alert) -> dict:
        """Representación JSON de una alerta (para las tools del agente)."""
        return {
            "id": alerta.id,
            "product_id": alerta.product_id,
            "location_id": alerta.location_id,
            "alert_type": alerta.alert_type,
            "severity": alerta.severity,
            "message": alerta.message,
            "details": alerta.details,
            "status": alerta.status,
            "created_at": alerta.created_at.isoformat(),
            "updated_at": alerta.updated_at.isoformat(),
        }

    @staticmethod
    def list_data(filters, limit=100) -> list:
        """Alertas ya filtradas y convertidas a dicts (tools del agente)."""
        return [AlertService.to_dict(a) for a in AlertService.list(filters)[:limit]]

    @staticmethod
    @transaction.atomic
    def upsert_from_analysis(alert_type, product_id, severity, message, details=None, location_id=None):
        """Crea o actualiza la alerta pendiente del mismo tipo/producto/ubicación.

        Devuelve (alerta, creada) para que el comando pueda informar altas y
        actualizaciones sin volver a consultar.
        """
        key = AlertService.dedup_key(alert_type, product_id, location_id)
        alerta = (
            Alert.objects.select_for_update()
            .filter(dedup_key=key, status=Alert.Status.PENDIENTE)
            .first()
        )
        if alerta is not None:
            alerta.severity = severity
            alerta.message = message
            alerta.details = details or {}
            alerta.save(update_fields=["severity", "message", "details", "updated_at"])
            return alerta, False

        alerta = Alert.objects.create(
            product_id=product_id,
            location_id=location_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            details=details or {},
            dedup_key=key,
        )
        return alerta, True

    @staticmethod
    def build_alerts():
        """Traduce la salida de los analyzers a candidatos de alerta (tabla del Paso 13).

        Cada candidato lleva los números que lo justifican en ``details`` (RN-B03).
        """
        from django.conf import settings

        cfg = RiskConfigService.resolve()
        min_stock = cfg.min_stock or 0
        umbral_agotamiento = getattr(settings, "DEPLETION_ALERT_THRESHOLD_DAYS", 7)
        hoy = as_of_date().isoformat()
        pedidos = {p.id: p.reorder_point for p in Product.objects.all().only("id", "reorder_point")}

        candidatos = []

        for r in StockoutAnalyzer.run(risk_min="ALTO"):
            ins = r["inputs"]
            severity = Alert.Severity.CRITICA if r["risk"] == "CRITICO" else Alert.Severity.ALTA
            candidatos.append({
                "alert_type": Alert.Type.DESABASTO,
                "product_id": r["product_id"],
                "severity": severity,
                "message": (
                    f"{r['product_name']}: desabasto {r['risk']} "
                    f"(stock {ins['stock']}, demanda {ins['daily_demand']}/día, "
                    f"cobertura {ins['days_of_cover']} días, entrega {ins['lead_time_days']} días)"
                ),
                "details": dict(ins, risk=r["risk"], product_name=r["product_name"]),
            })

        # BAJO_STOCK no depende del riesgo de desabasto: es el cruce de existencias
        # disponibles contra los umbrales configurados (RF-B15).
        stock = repo.stock_by_product()
        pendientes = repo.pending_by_product()
        nombres = dict(Product.objects.values_list("id", "name"))
        for pid, unidades in stock.items():
            punto = pedidos.get(pid) or 0
            umbrales = [u for u in (min_stock, punto) if u]
            if not umbrales:
                continue
            disponible = unidades - pendientes.get(pid, 0)
            if disponible >= min(umbrales):
                continue
            candidatos.append({
                "alert_type": Alert.Type.BAJO_STOCK,
                "product_id": pid,
                "severity": Alert.Severity.MEDIA,
                "message": (
                    f"{nombres.get(pid)}: disponible {disponible} por debajo del "
                    f"mínimo {min_stock} o del punto de reorden {punto}"
                ),
                "details": {"available": disponible, "stock": unidades,
                            "pending": pendientes.get(pid, 0), "min_stock": min_stock,
                            "reorder_point": punto, "product_name": nombres.get(pid),
                            "as_of": hoy},
            })

        for r in DepletionAnalyzer.run(risk_min="BAJO"):
            dias = r["inputs"]["depletion_days"]
            if dias is None or dias > umbral_agotamiento:
                continue
            candidatos.append({
                "alert_type": Alert.Type.AGOTAMIENTO_ESTIMADO,
                "product_id": r["product_id"],
                "severity": Alert.Severity.ALTA,
                "message": (
                    f"{r['product_name']}: agotamiento estimado en {dias} días "
                    f"({r['estimated_depletion_date']})"
                ),
                "details": dict(r, threshold_days=umbral_agotamiento),
            })

        for r in OverstockAnalyzer.run():
            candidatos.append({
                "alert_type": Alert.Type.SOBREINVENTARIO,
                "product_id": r["product_id"],
                "severity": Alert.Severity.BAJA,
                "message": (
                    f"{r['product_name']}: exceso de {r['excess_units']} unidades "
                    f"({r['excess_value']} de capital inmovilizado)"
                ),
                "details": dict(r, as_of=hoy),
            })

        for r in TurnoverAnalyzer.run():
            if r["classification"] not in ("BAJA_ROTACION", "SIN_MOVIMIENTO"):
                continue
            candidatos.append({
                "alert_type": Alert.Type.BAJA_ROTACION,
                "product_id": r["product_id"],
                "severity": Alert.Severity.BAJA,
                "message": (
                    f"{r['product_name']}: {r['classification']} "
                    f"(rotación {r['turnover']} en {r['inputs']['window_days']} días)"
                ),
                "details": dict(r),
            })

        for r in ExpirationAnalyzer.run():
            dias = r["inputs"]["days_remaining"]
            if r["severity"] == "CADUCADO":
                candidatos.append({
                    "alert_type": Alert.Type.PRODUCTO_CADUCADO,
                    "product_id": r["product_id"],
                    "location_id": Lot.objects.filter(
                        product_id=r["product_id"], lot_number=r["lot_number"]
                    ).values_list("location_id", flat=True).first(),
                    "severity": Alert.Severity.CRITICA,
                    "message": (
                        f"Lote {r['lot_number']} de {r['product_name']} caducado hace "
                        f"{abs(dias)} días ({r['expiration_date']})"
                    ),
                    "details": dict(r),
                })
            elif r["severity"] in ("MEDIO", "ALTO"):
                candidatos.append({
                    "alert_type": Alert.Type.CADUCIDAD_PROXIMA,
                    "product_id": r["product_id"],
                    "location_id": Lot.objects.filter(
                        product_id=r["product_id"], lot_number=r["lot_number"]
                    ).values_list("location_id", flat=True).first(),
                    "severity": (Alert.Severity.ALTA if r["severity"] == "ALTO"
                                 else Alert.Severity.MEDIA),
                    "message": (
                        f"Lote {r['lot_number']} de {r['product_name']} caduca en "
                        f"{dias} días ({r['expiration_date']})"
                    ),
                    "details": dict(r),
                })

        return candidatos