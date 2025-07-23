# reportes/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import ReporteManager
from .serializers import (
    ReporteParametrosSerializer,
    ProductosVendidosSerializer,
    VentasPeriodoSerializer,
    TopClientesSerializer,
    ComparativaPeriodosSerializer,
    ReporteRapidoSerializer,
    ProductoVendidoResponseSerializer,
    VentaPeriodoResponseSerializer,
    ResumenGeneralResponseSerializer,
    ClienteTopResponseSerializer,
    EfectividadOfertasResponseSerializer,
    ComparativaResponseSerializer,
)

from django.http import HttpResponse
import csv
import json
from datetime import datetime


class ReporteViewSet(viewsets.ViewSet):
    """
    ViewSet para generar reportes dinámicos de ventas y productos
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        method="get",
        query_serializer=ProductosVendidosSerializer,
        responses={
            200: openapi.Response(
                description="Lista de productos más vendidos",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "productos": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT),
                        ),
                        "parametros": openapi.Schema(type=openapi.TYPE_OBJECT),
                        "total_registros": openapi.Schema(type=openapi.TYPE_INTEGER),
                    },
                ),
            )
        },
        operation_description="Obtiene los productos más vendidos en un rango de fechas específico",
    )
    @action(detail=False, methods=["get"], url_path="productos-mas-vendidos")
    def productos_mas_vendidos(self, request):
        """
        Obtiene los productos más vendidos con filtros opcionales
        """
        serializer = ProductosVendidosSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # Extraer parámetros validados
        fecha_inicio = serializer.validated_data.get("fecha_inicio")
        fecha_fin = serializer.validated_data.get("fecha_fin")
        limite = serializer.validated_data.get("limite", 10)

        # Generar el reporte
        productos = ReporteManager.productos_mas_vendidos(
            fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, limite=limite
        )

        return Response(
            {
                "productos": productos,
                "parametros": {
                    "fecha_inicio": fecha_inicio,
                    "fecha_fin": fecha_fin,
                    "limite": limite,
                },
                "total_registros": len(productos),
            }
        )

    @swagger_auto_schema(
        method="get",
        query_serializer=VentasPeriodoSerializer,
        responses={200: "Ventas agrupadas por período"},
        operation_description="Obtiene las ventas agrupadas por día, semana, mes o año",
    )
    @action(detail=False, methods=["get"], url_path="ventas-por-periodo")
    def ventas_por_periodo(self, request):
        """
        Obtiene ventas agrupadas por período de tiempo
        """
        serializer = VentasPeriodoSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        fecha_inicio = serializer.validated_data.get("fecha_inicio")
        fecha_fin = serializer.validated_data.get("fecha_fin")
        agrupar_por = serializer.validated_data.get("agrupar_por", "dia")

        ventas = ReporteManager.ventas_por_periodo(
            fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, agrupar_por=agrupar_por
        )

        return Response(
            {
                "ventas": ventas,
                "parametros": {
                    "fecha_inicio": fecha_inicio,
                    "fecha_fin": fecha_fin,
                    "agrupar_por": agrupar_por,
                },
                "total_periodos": len(ventas),
            }
        )

    @swagger_auto_schema(
        method="get",
        query_serializer=ReporteParametrosSerializer,
        responses={200: "Resumen general de ventas"},
        operation_description="Obtiene un resumen general de las ventas en un período",
    )
    @action(detail=False, methods=["get"], url_path="resumen-general")
    def resumen_general(self, request):
        """
        Obtiene un resumen general de ventas
        """
        serializer = ReporteParametrosSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        fecha_inicio = serializer.validated_data.get("fecha_inicio")
        fecha_fin = serializer.validated_data.get("fecha_fin")

        resumen = ReporteManager.resumen_ventas_general(
            fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
        )

        return Response(
            {
                "resumen": resumen,
                "parametros": {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
            }
        )

    @swagger_auto_schema(
        method="get",
        query_serializer=TopClientesSerializer,
        responses={200: "Lista de mejores clientes"},
        operation_description="Obtiene los clientes que más han gastado",
    )
    @action(detail=False, methods=["get"], url_path="top-clientes")
    def top_clientes(self, request):
        """
        Obtiene los mejores clientes por volumen de compras
        """
        serializer = TopClientesSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        fecha_inicio = serializer.validated_data.get("fecha_inicio")
        fecha_fin = serializer.validated_data.get("fecha_fin")
        limite = serializer.validated_data.get("limite", 10)

        clientes = ReporteManager.top_clientes(
            fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, limite=limite
        )

        return Response(
            {
                "clientes": clientes,
                "parametros": {
                    "fecha_inicio": fecha_inicio,
                    "fecha_fin": fecha_fin,
                    "limite": limite,
                },
                "total_registros": len(clientes),
            }
        )

    @swagger_auto_schema(
        method="get",
        query_serializer=ReporteParametrosSerializer,
        responses={200: "Análisis de efectividad de ofertas"},
        operation_description="Analiza la efectividad de las ofertas en las ventas",
    )
    @action(detail=False, methods=["get"], url_path="efectividad-ofertas")
    def efectividad_ofertas(self, request):
        """
        Analiza la efectividad de las ofertas
        """
        serializer = ReporteParametrosSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        fecha_inicio = serializer.validated_data.get("fecha_inicio")
        fecha_fin = serializer.validated_data.get("fecha_fin")

        efectividad = ReporteManager.productos_con_ofertas_efectividad(
            fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
        )

        return Response(
            {
                "efectividad": efectividad,
                "parametros": {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
            }
        )

    @swagger_auto_schema(
        method="post",
        request_body=ComparativaPeriodosSerializer,
        responses={200: "Comparativa entre dos períodos"},
        operation_description="Compara las ventas entre dos períodos de tiempo",
    )
    @action(detail=False, methods=["post"], url_path="comparativa-periodos")
    def comparativa_periodos(self, request):
        """
        Compara las ventas entre dos períodos
        """
        serializer = ComparativaPeriodosSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fecha_inicio_1 = serializer.validated_data["fecha_inicio_1"]
        fecha_fin_1 = serializer.validated_data["fecha_fin_1"]
        fecha_inicio_2 = serializer.validated_data["fecha_inicio_2"]
        fecha_fin_2 = serializer.validated_data["fecha_fin_2"]

        comparativa = ReporteManager.comparativa_periodos(
            fecha_inicio_1, fecha_fin_1, fecha_inicio_2, fecha_fin_2
        )

        return Response(comparativa)

    @swagger_auto_schema(
        method="get",
        query_serializer=ReporteRapidoSerializer,
        responses={200: "Reporte completo predefinido"},
        operation_description="Genera un reporte completo para un período predefinido",
    )
    @action(detail=False, methods=["get"], url_path="reporte-rapido")
    def reporte_rapido(self, request):
        """
        Genera un reporte completo para períodos predefinidos
        """
        serializer = ReporteRapidoSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        periodo = serializer.validated_data["periodo"]
        fecha_inicio, fecha_fin = serializer.get_fechas_periodo(periodo)

        # Generar todos los reportes para el período
        resumen = ReporteManager.resumen_ventas_general(fecha_inicio, fecha_fin)
        productos_vendidos = ReporteManager.productos_mas_vendidos(
            fecha_inicio, fecha_fin, 10
        )
        top_clientes = ReporteManager.top_clientes(fecha_inicio, fecha_fin, 5)
        ventas_diarias = ReporteManager.ventas_por_periodo(
            fecha_inicio, fecha_fin, "dia"
        )
        efectividad = ReporteManager.productos_con_ofertas_efectividad(
            fecha_inicio, fecha_fin
        )

        return Response(
            {
                "periodo": periodo,
                "rango_fechas": {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
                "resumen_general": resumen,
                "productos_mas_vendidos": productos_vendidos,
                "top_clientes": top_clientes,
                "ventas_por_dia": ventas_diarias,
                "efectividad_ofertas": efectividad,
            }
        )

    @swagger_auto_schema(
        method="get",
        query_serializer=ProductosVendidosSerializer,
        responses={200: "Archivo CSV con productos más vendidos"},
        operation_description="Descarga un CSV con los productos más vendidos",
    )
    @action(detail=False, methods=["get"], url_path="exportar-productos-csv")
    def exportar_productos_csv(self, request):
        """
        Exporta los productos más vendidos a CSV
        """
        serializer = ProductosVendidosSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        fecha_inicio = serializer.validated_data.get("fecha_inicio")
        fecha_fin = serializer.validated_data.get("fecha_fin")
        limite = serializer.validated_data.get("limite", 10)

        productos = ReporteManager.productos_mas_vendidos(
            fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, limite=limite
        )

        # Crear respuesta CSV
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = (
            'attachment; filename="productos_mas_vendidos.csv"'
        )
        response["Access-Control-Expose-Headers"] = "Content-Disposition"

        writer = csv.writer(response)

        # Escribir encabezados
        writer.writerow(
            [
                "ID Producto",
                "Nombre Producto",
                "Precio Actual",
                "Stock Actual",
                "Cantidad Vendida",
                "Veces Comprado",
                "Ingreso Total",
                "Precio Promedio Venta",
            ]
        )

        # Escribir datos
        for producto in productos:
            writer.writerow(
                [
                    producto["producto__id"],
                    producto["producto__nombre"],
                    producto["producto__precio"],
                    producto["producto__stock"],
                    producto["cantidad_vendida"],
                    producto["veces_comprado"],
                    producto["ingreso_total"],
                    producto["precio_promedio_venta"],
                ]
            )

        return response

    @swagger_auto_schema(
        method="get",
        query_serializer=VentasPeriodoSerializer,
        responses={200: "Archivo CSV con ventas por período"},
        operation_description="Descarga un CSV con las ventas agrupadas por período",
    )
    @action(detail=False, methods=["get"], url_path="exportar-ventas-csv")
    def exportar_ventas_csv(self, request):
        """
        Exporta las ventas por período a CSV
        """
        serializer = VentasPeriodoSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        fecha_inicio = serializer.validated_data.get("fecha_inicio")
        fecha_fin = serializer.validated_data.get("fecha_fin")
        agrupar_por = serializer.validated_data.get("agrupar_por", "dia")

        ventas = ReporteManager.ventas_por_periodo(
            fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, agrupar_por=agrupar_por
        )

        # Crear respuesta CSV
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = (
            f'attachment; filename="ventas_por_{agrupar_por}.csv"'
        )
        response["Access-Control-Expose-Headers"] = "Content-Disposition"

        writer = csv.writer(response)

        # Escribir encabezados
        writer.writerow(
            [
                "Período",
                "Total Pedidos",
                "Total Ingresos",
                "Total Productos Vendidos",
                "Ingreso Promedio por Pedido",
                "Descuento Promedio (%)",
            ]
        )

        # Escribir datos
        for venta in ventas:
            writer.writerow(
                [
                    venta["periodo"].strftime("%Y-%m-%d %H:%M:%S"),
                    venta["total_pedidos"],
                    venta["total_ingresos"],
                    venta["total_productos_vendidos"],
                    venta["ingreso_promedio_pedido"],
                    venta["descuento_promedio"],
                ]
            )

        return response

    @swagger_auto_schema(
        method="get",
        query_serializer=ReporteRapidoSerializer,
        responses={200: "Archivo CSV con reporte completo"},
        operation_description="Descarga un CSV con un reporte completo predefinido",
    )
    @action(detail=False, methods=["get"], url_path="exportar-reporte-completo-csv")
    def exportar_reporte_completo_csv(self, request):
        """
        Exporta un reporte completo a CSV
        """
        serializer = ReporteRapidoSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        periodo = serializer.validated_data["periodo"]
        fecha_inicio, fecha_fin = serializer.get_fechas_periodo(periodo)

        # Generar datos
        resumen = ReporteManager.resumen_ventas_general(fecha_inicio, fecha_fin)
        productos_vendidos = ReporteManager.productos_mas_vendidos(
            fecha_inicio, fecha_fin, 20
        )

        # Crear respuesta CSV
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = (
            f'attachment; filename="reporte_completo_{periodo}.csv"'
        )
        response["Access-Control-Expose-Headers"] = "Content-Disposition"

        writer = csv.writer(response)

        # Sección: Resumen General
        writer.writerow(["=== RESUMEN GENERAL ==="])
        writer.writerow(["Período", periodo])
        writer.writerow(["Fecha Inicio", fecha_inicio.strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow(["Fecha Fin", fecha_fin.strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow([])

        writer.writerow(["Métrica", "Valor"])
        writer.writerow(["Total Pedidos", resumen.get("total_pedidos", 0)])
        writer.writerow(["Total Ingresos", resumen.get("total_ingresos", 0)])
        writer.writerow(["Ingreso Promedio", resumen.get("ingreso_promedio", 0)])
        writer.writerow(
            ["Descuento Promedio (%)", resumen.get("descuento_promedio", 0)]
        )
        writer.writerow(
            ["Total Productos Vendidos", resumen.get("total_productos_vendidos", 0)]
        )
        writer.writerow(
            ["Productos Únicos Vendidos", resumen.get("productos_unicos_vendidos", 0)]
        )
        writer.writerow(["Clientes Únicos", resumen.get("clientes_unicos", 0)])
        writer.writerow([])

        # Sección: Productos Más Vendidos
        writer.writerow(["=== PRODUCTOS MÁS VENDIDOS ==="])
        writer.writerow(
            ["ID", "Nombre", "Cantidad Vendida", "Veces Comprado", "Ingreso Total"]
        )

        for producto in productos_vendidos:
            writer.writerow(
                [
                    producto["producto__id"],
                    producto["producto__nombre"],
                    producto["cantidad_vendida"],
                    producto["veces_comprado"],
                    producto["ingreso_total"],
                ]
            )

        return response

    @swagger_auto_schema(
        method="get",
        responses={200: "Dashboard con métricas clave"},
        operation_description="Obtiene un dashboard con las métricas más importantes",
    )
    @action(detail=False, methods=["get"], url_path="dashboard")
    def dashboard(self, request):
        """
        Genera un dashboard con las métricas más importantes
        """
        from django.utils import timezone
        from datetime import timedelta

        ahora = timezone.now()

        # Períodos para el dashboard
        hoy_inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
        ayer_inicio = hoy_inicio - timedelta(days=1)
        semana_inicio = ahora - timedelta(days=7)
        mes_inicio = ahora - timedelta(days=30)

        # Métricas de hoy
        hoy = ReporteManager.resumen_ventas_general(hoy_inicio, ahora)

        # Métricas de ayer
        ayer = ReporteManager.resumen_ventas_general(
            ayer_inicio, hoy_inicio - timedelta(seconds=1)
        )

        # Métricas de la semana
        semana = ReporteManager.resumen_ventas_general(semana_inicio, ahora)

        # Métricas del mes
        mes = ReporteManager.resumen_ventas_general(mes_inicio, ahora)

        # Top productos del mes
        top_productos_mes = ReporteManager.productos_mas_vendidos(mes_inicio, ahora, 5)

        # Top clientes del mes
        top_clientes_mes = ReporteManager.top_clientes(mes_inicio, ahora, 5)

        # Ventas de los últimos 7 días
        ventas_ultimos_dias = ReporteManager.ventas_por_periodo(
            semana_inicio, ahora, "dia"
        )

        return Response(
            {
                "fecha_actualizacion": ahora,
                "metricas": {
                    "hoy": hoy,
                    "ayer": ayer,
                    "ultima_semana": semana,
                    "ultimo_mes": mes,
                },
                "top_productos_mes": top_productos_mes,
                "top_clientes_mes": top_clientes_mes,
                "ventas_ultimos_7_dias": ventas_ultimos_dias,
                "comparaciones": {
                    "pedidos_hoy_vs_ayer": {
                        "hoy": hoy.get("total_pedidos", 0),
                        "ayer": ayer.get("total_pedidos", 0),
                        "diferencia": hoy.get("total_pedidos", 0)
                        - ayer.get("total_pedidos", 0),
                    },
                    "ingresos_hoy_vs_ayer": {
                        "hoy": float(hoy.get("total_ingresos", 0) or 0),
                        "ayer": float(ayer.get("total_ingresos", 0) or 0),
                        "diferencia": float(hoy.get("total_ingresos", 0) or 0)
                        - float(ayer.get("total_ingresos", 0) or 0),
                    },
                },
            }
        )
