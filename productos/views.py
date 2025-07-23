from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from .models import Producto, Categoria, Autor, Genero, Editorial, Oferta
from productos.serializers import (
    ProductoSerializer,
    CategoriaSerializer,
    AutorSerializer,
    GeneroSerializer,
    EditorialSerializer,
    OfertaSerializer,
    OfertaDetalladaSerializer,
)

from usuarios.permissions import TienePermisoPersonalizado


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [TienePermisoPersonalizado]

    permiso_por_accion = {
        "list": "ver_productos",
        "retrieve": "ver_productos",
        "create": "crear_productos",
        "update": "editar_productos",
        "partial_update": "editar_productos",
        "destroy": "eliminar_productos",
    }

    def get_queryset(self):
        return Producto.objects.filter(is_active=True)

    @action(detail=False, methods=["get"], url_path="en-oferta")
    def productos_en_oferta(self, request):
        """Obtiene todos los productos que tienen ofertas vigentes"""
        productos_con_oferta = Producto.objects.filter(
            is_active=True,
            oferta__isnull=False,
            oferta__is_active=True,
            oferta__fecha_inicio__lte=timezone.now(),
            oferta__fecha_fin__gte=timezone.now(),
        )
        serializer = self.get_serializer(productos_con_oferta, many=True)
        return Response(serializer.data)

    @action(
        detail=True, methods=["post"], url_path="aplicar-oferta/(?P<oferta_id>[^/.]+)"
    )
    def aplicar_oferta(self, request, pk=None, oferta_id=None):
        """
        Aplica una oferta específica a un producto.
        URL: /productos/{producto_id}/aplicar-oferta/{oferta_id}/
        """
        producto = self.get_object()

        if not oferta_id:
            return Response(
                {"error": "Se requiere el ID de la oferta en la URL"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            oferta = Oferta.objects.get(id=oferta_id, is_active=True)
        except Oferta.DoesNotExist:
            return Response(
                {"error": "Oferta no encontrada o inactiva"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Verificar si ya tiene esta oferta
        if producto.oferta == oferta:
            return Response(
                {
                    "mensaje": f'El producto "{producto.nombre}" ya tiene aplicada la oferta "{oferta.nombre}"'
                },
                status=status.HTTP_200_OK,
            )

        producto.oferta = oferta
        producto.save()

        serializer = self.get_serializer(producto)
        return Response(
            {
                "mensaje": f'✅ Oferta "{oferta.nombre}" aplicada al producto "{producto.nombre}"',
                "descuento_aplicado": str(oferta.descuento),
                "precio_original": str(producto.precio),
                "precio_con_descuento": str(producto.get_precio_con_descuento()),
                "producto": serializer.data,
            }
        )

    @action(detail=True, methods=["delete"], url_path="quitar-oferta")
    def quitar_oferta(self, request, pk=None):
        """
        Quita la oferta de un producto.
        URL: /productos/{producto_id}/quitar-oferta/
        """
        producto = self.get_object()

        if not producto.oferta:
            return Response(
                {"error": "El producto no tiene oferta aplicada"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        nombre_oferta = producto.oferta.nombre
        descuento_removido = producto.oferta.descuento
        producto.oferta = None
        producto.save()

        serializer = self.get_serializer(producto)
        return Response(
            {
                "mensaje": f'✅ Oferta "{nombre_oferta}" removida del producto "{producto.nombre}"',
                "descuento_removido": str(descuento_removido),
                "precio_actual": str(producto.precio),
                "producto": serializer.data,
            }
        )


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [TienePermisoPersonalizado]

    permiso_por_accion = {
        "list": "ver_categorias",
        "create": "crear_categorias",
        "update": "editar_categorias",
        "partial_update": "editar_categorias",
        "destroy": "eliminar_categorias",
    }


class AutorViewSet(viewsets.ModelViewSet):
    queryset = Autor.objects.all()
    serializer_class = AutorSerializer
    permission_classes = [TienePermisoPersonalizado]

    permiso_por_accion = {
        "list": "ver_autores",
        "create": "crear_autores",
        "update": "editar_autores",
        "partial_update": "editar_autores",
        "destroy": "eliminar_autores",
    }


class GeneroViewSet(viewsets.ModelViewSet):
    queryset = Genero.objects.all()
    serializer_class = GeneroSerializer
    permission_classes = [TienePermisoPersonalizado]

    permiso_por_accion = {
        "list": "ver_generos",
        "create": "crear_generos",
        "update": "editar_generos",
        "partial_update": "editar_generos",
        "destroy": "eliminar_generos",
    }


class EditorialViewSet(viewsets.ModelViewSet):
    queryset = Editorial.objects.all()
    serializer_class = EditorialSerializer
    permission_classes = [TienePermisoPersonalizado]

    permiso_por_accion = {
        "list": "ver_editoriales",
        "create": "crear_editoriales",
        "update": "editar_editoriales",
        "partial_update": "editar_editoriales",
        "destroy": "eliminar_editoriales",
    }


class OfertaViewSet(viewsets.ModelViewSet):
    queryset = Oferta.objects.all()
    serializer_class = OfertaSerializer
    permission_classes = [TienePermisoPersonalizado]

    permiso_por_accion = {
        "list": "ver_ofertas",
        "retrieve": "ver_ofertas",
        "create": "crear_ofertas",
        "update": "editar_ofertas",
        "partial_update": "editar_ofertas",
        "destroy": "eliminar_ofertas",
    }

    def get_queryset(self):
        return Oferta.objects.filter(is_active=True)

    def get_serializer_class(self):
        """Usa el serializer detallado para retrieve"""
        if self.action == "retrieve":
            return OfertaDetalladaSerializer
        return OfertaSerializer

    @action(detail=False, methods=["get"], url_path="vigentes")
    def ofertas_vigentes(self, request):
        """
        Obtiene todas las ofertas vigentes (activas y dentro del rango de fechas).
        URL: /ofertas/vigentes/
        """
        ofertas_vigentes = Oferta.objects.filter(
            is_active=True,
            fecha_inicio__lte=timezone.now(),
            fecha_fin__gte=timezone.now(),
        )
        serializer = self.get_serializer(ofertas_vigentes, many=True)
        return Response({"count": ofertas_vigentes.count(), "ofertas": serializer.data})

    @action(detail=False, methods=["get"], url_path="proximas")
    def ofertas_proximas(self, request):
        """
        Obtiene ofertas que comenzarán próximamente.
        URL: /ofertas/proximas/
        """
        ofertas_proximas = Oferta.objects.filter(
            is_active=True, fecha_inicio__gt=timezone.now()
        ).order_by("fecha_inicio")
        serializer = self.get_serializer(ofertas_proximas, many=True)
        return Response({"count": ofertas_proximas.count(), "ofertas": serializer.data})

    @action(detail=False, methods=["get"], url_path="expiradas")
    def ofertas_expiradas(self, request):
        """
        Obtiene ofertas que ya han expirado.
        URL: /ofertas/expiradas/
        """
        ofertas_expiradas = Oferta.objects.filter(
            is_active=True, fecha_fin__lt=timezone.now()
        ).order_by("-fecha_fin")
        serializer = self.get_serializer(ofertas_expiradas, many=True)
        return Response(
            {"count": ofertas_expiradas.count(), "ofertas": serializer.data}
        )

    @action(detail=True, methods=["get"], url_path="productos")
    def productos_en_oferta(self, request, pk=None):
        """
        Obtiene todos los productos asociados a una oferta específica.
        URL: /ofertas/{oferta_id}/productos/
        """
        oferta = self.get_object()
        productos = oferta.productos.filter(is_active=True)
        serializer = ProductoSerializer(productos, many=True)
        return Response(
            {
                "oferta": {
                    "id": oferta.id,
                    "nombre": oferta.nombre,
                    "descuento": str(oferta.descuento),
                },
                "productos_count": productos.count(),
                "productos": serializer.data,
            }
        )

    @action(detail=True, methods=["post"], url_path="agregar-productos")
    def agregar_productos(self, request, pk=None):
        """
        Agrega múltiples productos a una oferta de una sola vez.
        URL: /ofertas/{oferta_id}/agregar-productos/
        Body: {"productos_ids": [1, 2, 3, 4, 5]}

        Útil para aplicar ofertas masivas (ej: "Todos los libros de ciencia ficción")
        """
        oferta = self.get_object()
        productos_ids = request.data.get("productos_ids", [])

        if not productos_ids:
            return Response(
                {
                    "error": 'Se requiere una lista de IDs de productos en el campo "productos_ids"'
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(productos_ids, list):
            return Response(
                {"error": 'El campo "productos_ids" debe ser una lista de números'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verificar que los productos existen y están activos
        productos = Producto.objects.filter(id__in=productos_ids, is_active=True)
        productos_encontrados = productos.count()
        productos_solicitados = len(productos_ids)

        if productos_encontrados == 0:
            return Response(
                {
                    "error": "No se encontraron productos válidos con los IDs proporcionados"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Aplicar la oferta a todos los productos encontrados
        productos_actualizados = productos.update(oferta=oferta)

        return Response(
            {
                "mensaje": f'✅ {productos_actualizados} productos agregados a la oferta "{oferta.nombre}"',
                "oferta_id": oferta.id,
                "oferta_nombre": oferta.nombre,
                "productos_solicitados": productos_solicitados,
                "productos_encontrados": productos_encontrados,
                "productos_actualizados": productos_actualizados,
                "descuento_aplicado": str(oferta.descuento),
            }
        )

    @action(detail=True, methods=["post"], url_path="quitar-productos")
    def quitar_productos(self, request, pk=None):
        """
        Quita múltiples productos de una oferta de una sola vez.
        URL: /ofertas/{oferta_id}/quitar-productos/
        Body: {"productos_ids": [1, 2]}

        Los productos vuelven a su precio normal (sin descuento).
        """
        oferta = self.get_object()
        productos_ids = request.data.get("productos_ids", [])

        if not productos_ids:
            return Response(
                {
                    "error": 'Se requiere una lista de IDs de productos en el campo "productos_ids"'
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(productos_ids, list):
            return Response(
                {"error": 'El campo "productos_ids" debe ser una lista de números'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Buscar productos que actualmente tienen esta oferta aplicada
        productos = Producto.objects.filter(
            id__in=productos_ids, oferta=oferta, is_active=True
        )
        productos_encontrados = productos.count()
        productos_solicitados = len(productos_ids)

        if productos_encontrados == 0:
            return Response(
                {
                    "error": f'No se encontraron productos con la oferta "{oferta.nombre}" aplicada'
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Quitar la oferta de los productos encontrados
        productos_actualizados = productos.update(oferta=None)

        return Response(
            {
                "mensaje": f'✅ {productos_actualizados} productos removidos de la oferta "{oferta.nombre}"',
                "oferta_id": oferta.id,
                "oferta_nombre": oferta.nombre,
                "productos_solicitados": productos_solicitados,
                "productos_encontrados": productos_encontrados,
                "productos_actualizados": productos_actualizados,
                "descuento_removido": str(oferta.descuento),
            }
        )

    def destroy(self, request, *args, **kwargs):
        """
        Desactiva una oferta (eliminación lógica).
        URL: DELETE /ofertas/{oferta_id}/

        La oferta se marca como inactiva pero no se elimina de la base de datos.
        Los productos que tenían esta oferta la mantienen pero ya no se aplica el descuento.
        """
        oferta = self.get_object()

        # Contar productos afectados antes de desactivar
        productos_afectados = oferta.productos.filter(is_active=True).count()

        # Desactivar la oferta
        oferta.is_active = False
        oferta.save()

        return Response(
            {
                "mensaje": f'✅ Oferta "{oferta.nombre}" desactivada correctamente',
                "oferta_id": oferta.id,
                "oferta_nombre": oferta.nombre,
                "productos_afectados": productos_afectados,
                "nota": "Los productos mantienen la referencia a la oferta pero el descuento ya no se aplica",
            },
            status=status.HTTP_200_OK,
        )  # Cambiado de 204 a 200 para incluir el mensaje
