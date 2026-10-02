from .models import ProductVendor, PurchaseOrderDetail


class PurchaseService:
    @staticmethod
    def list(product_id=None, vendor_id=None, estado=None, limit=100):
        """Órdenes de compra (detalle) filtradas (RF-B07). ``estado``: 1..4."""
        qs = PurchaseOrderDetail.objects.select_related("order", "order__vendor")
        if product_id:
            qs = qs.filter(product_id=product_id)
        if vendor_id:
            qs = qs.filter(order__vendor_id=vendor_id)
        if estado:
            qs = qs.filter(order__status=int(estado))
        qs = qs.order_by("-order__order_date")[:limit]
        return [
            {
                "order_id": r.order_id,
                "vendor_id": r.order.vendor_id,
                "vendor_name": r.order.vendor.name,
                "status": r.order.status,
                "order_date": r.order.order_date.isoformat(),
                "due_date": r.due_date.isoformat(),
                "product_id": r.product_id,
                "order_qty": r.order_qty,
                "received_qty": float(r.received_qty),
                "unit_price": float(r.unit_price),
            }
            for r in qs
        ]


class SupplierService:
    @staticmethod
    def list(product_id, limit=100):
        """Proveedores de un producto, ordenados por lead time (RF-B07)."""
        qs = (
            ProductVendor.objects.filter(product_id=product_id)
            .select_related("vendor")
            .order_by("average_lead_time")[:limit]
        )
        return [
            {
                "product_id": pv.product_id,
                "vendor_id": pv.vendor_id,
                "vendor_name": pv.vendor.name,
                "average_lead_time": pv.average_lead_time,
                "standard_price": float(pv.standard_price),
                "min_order_qty": pv.min_order_qty,
                "max_order_qty": pv.max_order_qty,
                "on_order_qty": pv.on_order_qty,
            }
            for pv in qs
        ]
