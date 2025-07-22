from django.db import models
from django.db.models import Sum, Count, Avg, F, Q
from django.utils import timezone
from datetime import datetime, timedelta
from productos.models import Producto
from pedidos.models import Pedido, DetallePedido
from usuarios.models import Usuario


class ReporteManager:
    """
    Manager para generar reportes dinámicos
    """

    @staticmethod
    def productos_mas_vendidos(fecha_inicio=None, fecha_fin=None, limite=10):
        """
        Obtiene los productos más vendidos en un rango de fechas
        """
        # Filtro base para detalles de pedidos
        queryset = DetallePedido.objects.select_related("producto")

        # Aplicar filtros de fecha si se proporcionan
        if fecha_inicio:
            queryset = queryset.filter(pedido__fecha_pedido__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(pedido__fecha_pedido__lte=fecha_fin)

        # Agrupar por producto y calcular métricas
        productos_vendidos = (
            queryset.values(
                "producto__id",
                "producto__nombre",
                "producto__precio",
                "producto__stock",
            )
            .annotate(
                cantidad_vendida=Sum("cantidad"),
                veces_comprado=Count("pedido__id"),
                ingreso_total=Sum(F("cantidad") * F("precio_unitario")),
                precio_promedio_venta=Avg("precio_unitario"),
            )
            .order_by("-cantidad_vendida")[:limite]
        )

        return list(productos_vendidos)

    @staticmethod
    def ventas_por_periodo(fecha_inicio=None, fecha_fin=None, agrupar_por="dia"):
        """
        Obtiene ventas agrupadas por período (día, semana, mes)
        """
        queryset = Pedido.objects.filter(activo=True)

        # Aplicar filtros de fecha
        if fecha_inicio:
            queryset = queryset.filter(fecha_pedido__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(fecha_pedido__lte=fecha_fin)

        # Configurar agrupación según el período
        if agrupar_por == "dia":
            truncate_date = "day"
        elif agrupar_por == "semana":
            truncate_date = "week"
        elif agrupar_por == "mes":
            truncate_date = "month"
        elif agrupar_por == "año":
            truncate_date = "year"
        else:
            truncate_date = "day"

        # Agrupar y calcular métricas
        from django.db.models import DateTimeField
        from django.db.models.functions import Trunc

        ventas = (
            queryset.annotate(
                periodo=Trunc(
                    "fecha_pedido", truncate_date, output_field=DateTimeField()
                )
            )
            .values("periodo")
            .annotate(
                total_pedidos=Count("id"),
                total_ingresos=Sum("total"),
                total_productos_vendidos=Sum("detalles__cantidad"),
                ingreso_promedio_pedido=Avg("total"),
                descuento_promedio=Avg("descuento"),
            )
            .order_by("periodo")
        )

        return list(ventas)

    @staticmethod
    def resumen_ventas_general(fecha_inicio=None, fecha_fin=None):
        """
        Obtiene un resumen general de ventas
        """
        queryset = Pedido.objects.filter(activo=True)

        # Aplicar filtros de fecha
        if fecha_inicio:
            queryset = queryset.filter(fecha_pedido__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(fecha_pedido__lte=fecha_fin)

        # Calcular métricas generales
        resumen = queryset.aggregate(
            total_pedidos=Count("id"),
            total_ingresos=Sum("total"),
            ingreso_promedio=Avg("total"),
            descuento_promedio=Avg("descuento"),
            total_productos_vendidos=Sum("detalles__cantidad"),
        )

        # Calcular productos únicos vendidos
        productos_unicos = (
            DetallePedido.objects.filter(pedido__in=queryset)
            .values("producto")
            .distinct()
            .count()
        )

        resumen["productos_unicos_vendidos"] = productos_unicos

        # Calcular clientes únicos
        clientes_unicos = queryset.values("usuario").distinct().count()
        resumen["clientes_unicos"] = clientes_unicos

        return resumen

    @staticmethod
    def top_clientes(fecha_inicio=None, fecha_fin=None, limite=10):
        """
        Obtiene los clientes que más han comprado
        """
        queryset = Pedido.objects.filter(activo=True).select_related("usuario")

        # Aplicar filtros de fecha
        if fecha_inicio:
            queryset = queryset.filter(fecha_pedido__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(fecha_pedido__lte=fecha_fin)

        # Agrupar por cliente
        top_clientes = (
            queryset.values("usuario__id", "usuario__nombre_completo", "usuario__email")
            .annotate(
                total_pedidos=Count("id"),
                total_gastado=Sum("total"),
                gasto_promedio=Avg("total"),
                total_productos_comprados=Sum("detalles__cantidad"),
            )
            .order_by("-total_gastado")[:limite]
        )

        return list(top_clientes)

    @staticmethod
    def productos_con_ofertas_efectividad(fecha_inicio=None, fecha_fin=None):
        """
        Analiza la efectividad de las ofertas en las ventas
        """
        queryset = DetallePedido.objects.select_related("producto")

        # Aplicar filtros de fecha
        if fecha_inicio:
            queryset = queryset.filter(pedido__fecha_pedido__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(pedido__fecha_pedido__lte=fecha_fin)

        # Productos con ofertas
        con_ofertas = (
            queryset.filter(descuento_oferta__gt=0)
            .values("producto__id", "producto__nombre", "nombre_oferta")
            .annotate(
                cantidad_vendida=Sum("cantidad"),
                ingreso_con_descuento=Sum(F("cantidad") * F("precio_unitario")),
                ahorro_total_clientes=Sum(F("cantidad") * F("descuento_oferta")),
                ventas_count=Count("pedido__id"),
            )
        )

        # Productos sin ofertas
        sin_ofertas = (
            queryset.filter(descuento_oferta=0)
            .values("producto__id", "producto__nombre")
            .annotate(
                cantidad_vendida=Sum("cantidad"),
                ingreso_total=Sum(F("cantidad") * F("precio_unitario")),
                ventas_count=Count("pedido__id"),
            )
        )

        return {
            "productos_con_ofertas": list(con_ofertas),
            "productos_sin_ofertas": list(sin_ofertas),
        }

    @staticmethod
    def comparativa_periodos(fecha_inicio_1, fecha_fin_1, fecha_inicio_2, fecha_fin_2):
        """
        Compara las ventas entre dos períodos
        """
        # Período 1
        periodo_1 = ReporteManager.resumen_ventas_general(fecha_inicio_1, fecha_fin_1)

        # Período 2
        periodo_2 = ReporteManager.resumen_ventas_general(fecha_inicio_2, fecha_fin_2)

        # Calcular diferencias y porcentajes
        comparativa = {}
        for key in periodo_1.keys():
            if periodo_1[key] is not None and periodo_2[key] is not None:
                diferencia = periodo_1[key] - periodo_2[key]
                if periodo_2[key] != 0:
                    porcentaje_cambio = (diferencia / periodo_2[key]) * 100
                else:
                    porcentaje_cambio = 0 if diferencia == 0 else float("inf")

                comparativa[key] = {
                    "periodo_1": periodo_1[key],
                    "periodo_2": periodo_2[key],
                    "diferencia": diferencia,
                    "porcentaje_cambio": round(porcentaje_cambio, 2),
                }

        return {
            "periodo_1": {
                "fecha_inicio": fecha_inicio_1,
                "fecha_fin": fecha_fin_1,
                "datos": periodo_1,
            },
            "periodo_2": {
                "fecha_inicio": fecha_inicio_2,
                "fecha_fin": fecha_fin_2,
                "datos": periodo_2,
            },
            "comparativa": comparativa,
        }


# Modelo para guardar reportes generados (opcional, para cache)
class ReporteGuardado(models.Model):
    TIPOS_REPORTE = [
        ("productos_vendidos", "Productos Más Vendidos"),
        ("ventas_periodo", "Ventas por Período"),
        ("resumen_general", "Resumen General"),
        ("top_clientes", "Top Clientes"),
        ("efectividad_ofertas", "Efectividad de Ofertas"),
        ("comparativa", "Comparativa de Períodos"),
    ]

    tipo_reporte = models.CharField(max_length=50, choices=TIPOS_REPORTE)
    nombre = models.CharField(max_length=200)
    parametros = models.JSONField(help_text="Parámetros usados para generar el reporte")
    datos = models.JSONField(help_text="Datos del reporte generado")
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    generado_por = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True
    )
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["-fecha_generacion"]
        verbose_name = "Reporte Guardado"
        verbose_name_plural = "Reportes Guardados"

    def __str__(self):
        return f"{self.get_tipo_reporte_display()} - {self.nombre}"
