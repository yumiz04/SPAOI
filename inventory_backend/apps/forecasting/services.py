from datetime import timedelta

from django.db import transaction
from decimal import Decimal

from apps.analytics.models import AnalysisRecord
from apps.core.dates import as_of_date
from apps.products.models import Product
from apps.sales.services import SalesService
from .models import Forecast
from .models_ses import ses_confidence, ses_forecast

MODEL_NAME = "ses"
MODEL_VERSION = "1.0.0"
DIAS_MINIMOS = 14


class ForecastService:
    @staticmethod
    def build_daily_series(product_id: int, historical_days: int):
        """Serie diaria de unidades con los días sin venta rellenos con 0 (P4).

        La agregación es SQL (SalesService.daily_units); el relleno de huecos es
        necesariamente secuencial porque el modelo consume la serie completa.
        """
        fin = as_of_date()
        inicio = fin - timedelta(days=historical_days)
        por_dia = SalesService.daily_units(product_id, inicio, fin)

        serie, fechas = [], []
        for offset in range(historical_days):
            dia = inicio + timedelta(days=offset + 1)  # días con venta, inclusivo el final
            fechas.append(dia)
            serie.append(float(por_dia.get(dia, 0)))
        return serie, fechas

    @staticmethod
    def forecast(product_id: int, historical_days: int, forecast_days: int, alpha: float = 0.3):
        producto = Product.objects.filter(pk=product_id).values("id", "name").first()
        if producto is None:
            from apps.core.exceptions import NotFoundError

            raise NotFoundError("PRODUCT_NOT_FOUND", f"No existe el producto {product_id}")

        serie, fechas = ForecastService.build_daily_series(product_id, historical_days)
        level, sigma = ses_forecast(serie, alpha)
        confianza = round(ses_confidence(level, sigma), 3)
        z = 1.96

        inicio_pronostico = as_of_date() + timedelta(days=1)
        filas = []
        for i in range(forecast_days):
            dia = inicio_pronostico + timedelta(days=i)
            filas.append({
                "forecast_date": dia,
                "quantity": round(level, 2),
                "lower": round(max(0.0, level - z * sigma), 2),
                "upper": round(level + z * sigma, 2),
            })

        resultado = {
            "product_id": product_id,
            "product_name": producto["name"],
            "model_name": MODEL_NAME,
            "model_version": MODEL_VERSION,
            "as_of": as_of_date().isoformat(),
            "historical_days": historical_days,
            "forecast_days": forecast_days,
            "level": round(level, 3),
            "sigma": round(sigma, 3),
            "confidence": confianza,
            "inputs": {
                "alpha": alpha,
                "days_with_data": sum(1 for v in serie if v > 0),
                "total_units": sum(serie),
                "series_start": fechas[0].isoformat() if fechas else None,
                "series_end": fechas[-1].isoformat() if fechas else None,
                "z": z,
            },
            "forecast": [
                {
                    "forecast_date": f["forecast_date"].isoformat(),
                    "quantity": f["quantity"],
                    "lower": f["lower"],
                    "upper": f["upper"],
                }
                for f in filas
            ],
        }

        dias_con_datos = resultado["inputs"]["days_with_data"]
        if dias_con_datos < DIAS_MINIMOS:
            resultado["warning"] = "Historial insuficiente"

        ForecastService.persist(product_id, filas, confianza)
        return resultado

    @staticmethod
    @transaction.atomic
    def persist(product_id: int, filas, confianza: float):
        """RN-B05: se conservan el pronóstico diario y la corrida completa."""
        Forecast.objects.filter(
            product_id=product_id, model_name=MODEL_NAME, model_version=MODEL_VERSION,
            forecast_date__in=[f["forecast_date"] for f in filas],
        ).delete()
        Forecast.objects.bulk_create([
            Forecast(
                product_id=product_id,
                forecast_date=f["forecast_date"],
                forecast_quantity=Decimal(str(f["quantity"])),
                model_name=MODEL_NAME,
                model_version=MODEL_VERSION,
                confidence=Decimal(str(confianza)),
            )
            for f in filas
        ])

    @staticmethod
    @transaction.atomic
    def persist_analysis(resultado: dict):
        AnalysisRecord.objects.create(
            analysis_type="forecast",
            product_id=resultado["product_id"],
            parameters={
                "historical_days": resultado["historical_days"],
                "forecast_days": resultado["forecast_days"],
                "model_name": resultado["model_name"],
                "model_version": resultado["model_version"],
                "alpha": resultado["inputs"]["alpha"],
            },
            result={
                "level": resultado["level"],
                "sigma": resultado["sigma"],
                "confidence": resultado["confidence"],
                "forecast": resultado["forecast"],
                "warning": resultado.get("warning"),
            },
            algorithm_version=resultado["model_version"],
        )