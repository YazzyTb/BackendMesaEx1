# reportes/serializers.py
from rest_framework import serializers
from datetime import datetime, timedelta
from django.utils import timezone


class ReporteParametrosSerializer(serializers.Serializer):
    """
    Serializer para validar los parámetros comunes de los reportes
    """

    fecha_inicio = serializers.DateTimeField(
        required=False,
        help_text="Fecha de inicio del reporte (formato: YYYY-MM-DD o YYYY-MM-DD HH:MM:SS)",
    )
    fecha_fin = serializers.DateTimeField(
        required=False,
        help_text="Fecha de fin del reporte (formato: YYYY-MM-DD o YYYY-MM-DD HH:MM:SS)",
    )

    def validate(self, data):
        fecha_inicio = data.get("fecha_inicio")
        fecha_fin = data.get("fecha_fin")

        # Si se proporciona fecha_fin pero no fecha_inicio, usar hace 30 días
        if fecha_fin and not fecha_inicio:
            data["fecha_inicio"] = fecha_fin - timedelta(days=30)

        # Si se proporciona fecha_inicio pero no fecha_fin, usar fecha actual
        if fecha_inicio and not fecha_fin:
            data["fecha_fin"] = timezone.now()

        # Validar que fecha_inicio sea anterior a fecha_fin
        if fecha_inicio and fecha_fin and fecha_inicio >= fecha_fin:
            raise serializers.ValidationError(
                "La fecha de inicio debe ser anterior a la fecha de fin."
            )

        return data


class ProductosVendidosSerializer(ReporteParametrosSerializer):
    """
    Serializer para el reporte de productos más vendidos
    """

    limite = serializers.IntegerField(
        default=10,
        min_value=1,
        max_value=100,
        help_text="Número máximo de productos a mostrar (1-100)",
    )


class VentasPeriodoSerializer(ReporteParametrosSerializer):
    """
    Serializer para el reporte de ventas por período
    """

    OPCIONES_AGRUPACION = [
        ("dia", "Por Día"),
        ("semana", "Por Semana"),
        ("mes", "Por Mes"),
        ("año", "Por Año"),
    ]

    agrupar_por = serializers.ChoiceField(
        choices=OPCIONES_AGRUPACION,
        default="dia",
        help_text="Forma de agrupar las ventas",
    )


class TopClientesSerializer(ReporteParametrosSerializer):
    """
    Serializer para el reporte de top clientes
    """

    limite = serializers.IntegerField(
        default=10,
        min_value=1,
        max_value=50,
        help_text="Número máximo de clientes a mostrar (1-50)",
    )


class ComparativaPeriodosSerializer(serializers.Serializer):
    """
    Serializer para comparar dos períodos de tiempo
    """

    # Primer período
    fecha_inicio_1 = serializers.DateTimeField(
        help_text="Fecha de inicio del primer período"
    )
    fecha_fin_1 = serializers.DateTimeField(help_text="Fecha de fin del primer período")

    # Segundo período
    fecha_inicio_2 = serializers.DateTimeField(
        help_text="Fecha de inicio del segundo período"
    )
    fecha_fin_2 = serializers.DateTimeField(
        help_text="Fecha de fin del segundo período"
    )

    def validate(self, data):
        # Validar primer período
        if data["fecha_inicio_1"] >= data["fecha_fin_1"]:
            raise serializers.ValidationError(
                "La fecha de inicio del primer período debe ser anterior a su fecha de fin."
            )

        # Validar segundo período
        if data["fecha_inicio_2"] >= data["fecha_fin_2"]:
            raise serializers.ValidationError(
                "La fecha de inicio del segundo período debe ser anterior a su fecha de fin."
            )

        return data


class ReporteRapidoSerializer(serializers.Serializer):
    """
    Serializer para generar reportes rápidos predefinidos
    """

    PERIODOS_PREDEFINIDOS = [
        ("hoy", "Hoy"),
        ("ayer", "Ayer"),
        ("ultima_semana", "Última Semana"),
        ("ultimo_mes", "Último Mes"),
        ("ultimo_trimestre", "Último Trimestre"),
        ("ultimo_año", "Último Año"),
        ("este_mes", "Este Mes"),
        ("este_año", "Este Año"),
    ]

    periodo = serializers.ChoiceField(
        choices=PERIODOS_PREDEFINIDOS, help_text="Período predefinido para el reporte"
    )

    def get_fechas_periodo(self, periodo):
        """
        Convierte el período predefinido en fechas específicas
        """
        ahora = timezone.now()
        hoy_inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)

        if periodo == "hoy":
            return hoy_inicio, ahora

        elif periodo == "ayer":
            ayer_inicio = hoy_inicio - timedelta(days=1)
            ayer_fin = hoy_inicio - timedelta(seconds=1)
            return ayer_inicio, ayer_fin

        elif periodo == "ultima_semana":
            inicio = ahora - timedelta(days=7)
            return inicio, ahora

        elif periodo == "ultimo_mes":
            inicio = ahora - timedelta(days=30)
            return inicio, ahora

        elif periodo == "ultimo_trimestre":
            inicio = ahora - timedelta(days=90)
            return inicio, ahora

        elif periodo == "ultimo_año":
            inicio = ahora - timedelta(days=365)
            return inicio, ahora

        elif periodo == "este_mes":
            inicio_mes = hoy_inicio.replace(day=1)
            return inicio_mes, ahora

        elif periodo == "este_año":
            inicio_año = hoy_inicio.replace(month=1, day=1)
            return inicio_año, ahora

        else:
            # Por defecto, último mes
            inicio = ahora - timedelta(days=30)
            return inicio, ahora


# Serializers para las respuestas (solo lectura)
class ProductoVendidoResponseSerializer(serializers.Serializer):
    """
    Serializer para la respuesta de productos vendidos
    """

    producto__id = serializers.IntegerField()
    producto__nombre = serializers.CharField()
    producto__precio = serializers.DecimalField(max_digits=10, decimal_places=2)
    producto__stock = serializers.IntegerField()
    cantidad_vendida = serializers.IntegerField()
    veces_comprado = serializers.IntegerField()
    ingreso_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    precio_promedio_venta = serializers.DecimalField(max_digits=10, decimal_places=2)


class VentaPeriodoResponseSerializer(serializers.Serializer):
    """
    Serializer para la respuesta de ventas por período
    """

    periodo = serializers.DateTimeField()
    total_pedidos = serializers.IntegerField()
    total_ingresos = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_productos_vendidos = serializers.IntegerField()
    ingreso_promedio_pedido = serializers.DecimalField(max_digits=10, decimal_places=2)
    descuento_promedio = serializers.DecimalField(max_digits=5, decimal_places=2)


class ResumenGeneralResponseSerializer(serializers.Serializer):
    """
    Serializer para la respuesta del resumen general
    """

    total_pedidos = serializers.IntegerField()
    total_ingresos = serializers.DecimalField(max_digits=12, decimal_places=2)
    ingreso_promedio = serializers.DecimalField(max_digits=10, decimal_places=2)
    descuento_promedio = serializers.DecimalField(max_digits=5, decimal_places=2)
    total_productos_vendidos = serializers.IntegerField()
    productos_unicos_vendidos = serializers.IntegerField()
    clientes_unicos = serializers.IntegerField()


class ClienteTopResponseSerializer(serializers.Serializer):
    """
    Serializer para la respuesta de top clientes
    """

    usuario__id = serializers.IntegerField()
    usuario__nombre_completo = serializers.CharField()
    usuario__email = serializers.EmailField()
    total_pedidos = serializers.IntegerField()
    total_gastado = serializers.DecimalField(max_digits=12, decimal_places=2)
    gasto_promedio = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_productos_comprados = serializers.IntegerField()


class EfectividadOfertasResponseSerializer(serializers.Serializer):
    """
    Serializer para la respuesta de efectividad de ofertas
    """

    productos_con_ofertas = serializers.ListField(child=serializers.DictField())
    productos_sin_ofertas = serializers.ListField(child=serializers.DictField())


class ComparativaResponseSerializer(serializers.Serializer):
    """
    Serializer para la respuesta de comparativa de períodos
    """

    periodo_1 = serializers.DictField()
    periodo_2 = serializers.DictField()
    comparativa = serializers.DictField()
