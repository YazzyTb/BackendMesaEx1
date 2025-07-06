from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import CarritoSerializer
from rest_framework.permissions import IsAuthenticated
from itertools import combinations
import requests
from django.conf import settings

from .models import Carrito, DetalleCarrito
from rest_framework.exceptions import ValidationError
from .models import Pedido, DetallePedido
from .serializers import PedidoSerializer, DetallePedidoSerializer, DetalleCarritoSerializer
from drf_yasg.utils import swagger_auto_schema
from .schemas import (
    carrito_response, carrito_request, 
    detalle_carrito_response, detalle_carrito_request,
    pedido_conversion_response
)

class DetallePedidoViewSet(viewsets.ModelViewSet):
    queryset = DetallePedido.objects.all()
    serializer_class = DetallePedidoSerializer

    def perform_create(self, serializer):
        detalle = serializer.save()  # Guardamos el detalle
        # Obtenemos el pedido asociado al detalle
        pedido = detalle.pedido
        pedido.calcular_total()  # Recalcular el total después de agregar el detalle
        pedido.save()  # Guardar el pedido con el nuevo total


# ViewSet para Pedidos
class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer

    def perform_create(self, serializer):
        pedido = serializer.save()
        pedido.calcular_total()
        pedido.save()

    def get_queryset(self):
        # Filtrar pedidos por usuario autenticado si es un usuario normal
        if self.request.user.is_authenticated:
            if hasattr(self.request.user, 'rol') and self.request.user.rol and self.request.user.rol.nombre == 'Administrador':
                # Si es administrador, puede ver todos los pedidos
                return Pedido.objects.all()
            else:
                # Si es un usuario normal, solo ve sus propios pedidos
                return Pedido.objects.filter(usuario=self.request.user)
        return Pedido.objects.none()

    @action(detail=True, methods=['post'], url_path='calcular-total')
    def calcular_total(self, request, pk=None):
        pedido = self.get_object()
        pedido.calcular_total()
        pedido.save()
        return Response({'total_actualizado': str(pedido.total)})

    @action(detail=True, methods=['post'], url_path='calificar')
    def calificar(self, request, pk=None):
        pedido = self.get_object()

        # Obtenemos la calificación del cuerpo de la solicitud
        calificacion = request.data.get('calificacion')

        if calificacion is None:
            return Response({'detail': 'Debe proporcionar una calificación.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validamos que la calificación esté en el rango correcto (1-5)
        if not (1 <= calificacion <= 5):
            return Response({'detail': 'La calificación debe estar entre 1 y 5.'}, status=status.HTTP_400_BAD_REQUEST)

        # Actualizamos la calificación
        pedido.calificacion = calificacion
        pedido.save()

        return Response({'detail': 'Calificación actualizada con éxito.'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='combinaciones-ml', permission_classes=[])
    def combinaciones_ml(self, request):
        """
        Genera datos para machine learning donde:
        - Target: Exactamente 1 producto
        - Input: Todos los demás productos del pedido
        
        Exporta datos en formato JSON o CSV con solo dos columnas: input_productos y target_producto
        """
        format_type = request.query_params.get('format', 'json')
        
        # Obtener pedidos con prefetch para optimizar
        pedidos = Pedido.objects.prefetch_related('detalles__producto').all()
        
        resultado = []
        
        for pedido in pedidos:
            productos = list(pedido.detalles.values_list('producto_id', flat=True))
            
            # Necesitamos al menos 2 productos (1 para input y 1 para target)
            if len(productos) < 2:
                continue
            
            # Para cada producto, ese producto es el target y el resto es el input
            for target_idx, target_product in enumerate(productos):
                # El input es todos los productos excepto el target
                input_products = [p for idx, p in enumerate(productos) if idx != target_idx]
                
                resultado.append({
                    "input": input_products,
                    "target": target_product  # Target es solo un producto
                })
        
        # Generación de CSV si se solicita
        if format_type.lower() == 'csv':
            import csv
            import json
            from django.http import HttpResponse
            
            # Configurar la respuesta HTTP para forzar la descarga
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="recomendaciones_ml.csv"'
            response['Access-Control-Expose-Headers'] = 'Content-Disposition'
            
            # Configurar el writer para que use comillas dobles
            writer = csv.writer(response, quoting=csv.QUOTE_ALL)
            writer.writerow(['input', 'target'])
            
            for item in resultado:
                # Convertir input y target a formato JSON como strings
                input_json = json.dumps(item['input'])
                target_json = json.dumps([item['target']])  # Convertir a lista para mantener formato consistente
                
                writer.writerow([
                    input_json,
                    target_json
                ])
            
            return response
        
        # Para JSON, mantenemos la estructura de lista
        return Response(resultado)

    @action(detail=False, methods=['get'], url_path='descargar-ml-csv', permission_classes=[])
    def descargar_ml_csv(self, request):
        """
        Descarga directamente un archivo CSV con datos para machine learning:
        - Target: Exactamente 1 producto
        - Input: Todos los demás productos del pedido
        """
        # Obtener pedidos con prefetch para optimizar
        pedidos = Pedido.objects.prefetch_related('detalles__producto').all()
        
        resultado = []
        
        for pedido in pedidos:
            productos = list(pedido.detalles.values_list('producto_id', flat=True))
            
            # Necesitamos al menos 2 productos (1 para input y 1 para target)
            if len(productos) < 2:
                continue
            
            # Para cada producto, ese producto es el target y el resto es el input
            for target_idx, target_product in enumerate(productos):
                # El input es todos los productos excepto el target
                input_products = [p for idx, p in enumerate(productos) if idx != target_idx]
                
                resultado.append({
                    "input": input_products,
                    "target": target_product
                })
        
        # Generar CSV
        import csv
        import json
        from django.http import HttpResponse
        
        # Configurar la respuesta HTTP para forzar la descarga
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="recomendaciones_ml.csv"'
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        
        # Configurar el writer para que use comillas dobles
        writer = csv.writer(response, quoting=csv.QUOTE_ALL)
        writer.writerow(['input', 'target'])
        
        for item in resultado:
            # Convertir input y target a formato JSON como strings
            input_json = json.dumps(item['input'])
            target_json = json.dumps([item['target']])  # Convertir a lista para mantener formato consistente
            
            writer.writerow([
                input_json,
                target_json
            ])
        
        return response

    @swagger_auto_schema(responses={200: PedidoSerializer(many=True)})
    @action(detail=False, methods=['get'], url_path='mis-pedidos', permission_classes=[IsAuthenticated])
    def mis_pedidos(self, request):
        """
        Obtiene todos los pedidos del usuario autenticado.
        """
        if not request.user.is_authenticated:
            return Response({"error": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)
            
        pedidos = Pedido.objects.filter(usuario=request.user).order_by('-fecha_pedido')
        serializer = self.get_serializer(pedidos, many=True)
        return Response(serializer.data)

class CarritoViewSet(viewsets.ModelViewSet):
    queryset = Carrito.objects.all()
    serializer_class = CarritoSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(responses={200: carrito_response})
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(responses={200: carrito_response})
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
        
    @swagger_auto_schema(request_body=carrito_request, responses={201: carrito_response})
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        # Manejar el caso de Swagger cuando no hay usuario autenticado
        if not self.request.user.is_authenticated:
            return Carrito.objects.none()
        return Carrito.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    @swagger_auto_schema(responses={200: carrito_response})
    @action(detail=False, methods=['get'], url_path='activo')
    def obtener_carrito_activo(self, request):
        # Manejar el caso de Swagger cuando no hay usuario autenticado
        if not request.user.is_authenticated:
            return Response({"error": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)
            
        carrito, creado = Carrito.objects.get_or_create(usuario=request.user, activo=True)
        serializer = self.get_serializer(carrito)
        return Response(serializer.data)

    @swagger_auto_schema(responses={200: pedido_conversion_response})
    @action(detail=True, methods=['post'], url_path='convertir-a-pedido')
    def convertir_a_pedido(self, request, pk=None):
        # Manejar el caso de Swagger cuando no hay usuario autenticado
        if not request.user.is_authenticated:
            return Response({"error": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)
            
        carrito = self.get_object()
        pedido = carrito.convertir_a_pedido()
        return Response({
            'mensaje': 'Carrito convertido a pedido exitosamente.',
            'pedido_id': pedido.id
        })

    @swagger_auto_schema(responses={200: '{"mensaje": "Carrito vaciado exitosamente."}'})
    @action(detail=True, methods=['delete'], url_path='vaciar')
    def vaciar_carrito(self, request, pk=None):
        """
        Desactiva lógicamente todos los productos del carrito.
        """
        try:
            carrito = self.get_object()
            
            # Verificar que el carrito pertenece al usuario actual
            if carrito.usuario != request.user:
                return Response(
                    {"error": "No tiene permiso para modificar este carrito"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Obtener la cantidad de productos a desactivar
            detalles_activos = carrito.detalles.filter(is_active=True)
            cantidad_productos = detalles_activos.count()
            
            # Desactivar lógicamente todos los detalles del carrito
            detalles_activos.update(is_active=False)
            
            return Response({
                "mensaje": f"Carrito vaciado exitosamente. Se desactivaron {cantidad_productos} productos."
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error al vaciar el carrito: {str(e)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        responses={
            200: "Lista de productos recomendados basados en los productos del carrito"
        }
    )
    @action(detail=True, methods=['get'], url_path='recomendaciones')
    def obtener_recomendaciones(self, request, pk=None):
        """
        Obtiene recomendaciones de productos basadas en los productos del carrito.
        Este endpoint envía los IDs de los productos del carrito a un microservicio
        de recomendaciones y devuelve los productos recomendados.
        """
        try:
            carrito = self.get_object()
            
            # Verificar que el carrito pertenece al usuario actual
            if carrito.usuario != request.user:
                return Response(
                    {"error": "No tiene permiso para acceder a este carrito"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Obtener solo los detalles activos y extraer los IDs de los productos
            producto_ids = list(carrito.detalles.filter(is_active=True).values_list('producto_id', flat=True))
            
            # Si no hay productos en el carrito, devolver respuesta vacía
            if not producto_ids:
                return Response(
                    {"mensaje": "No hay productos en el carrito para generar recomendaciones."}, 
                    status=status.HTTP_200_OK
                )
            
            # Enviar los IDs de los productos al microservicio de recomendaciones
            try:
                # URL del microservicio de recomendaciones
                ml_service_url = settings.RECOMMENDATION_SERVICE_URL
                
                # Preparar los datos para enviar
                data = {
                    "input": producto_ids
                }
                
                # Realizar la petición al microservicio
                response = requests.post(ml_service_url, json=data, timeout=5)
                
                # Verificar si la respuesta es exitosa
                if response.status_code != 200:
                    return Response(
                        {"error": f"Error al obtener recomendaciones: {response.text}"}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                # Obtener los IDs de los productos recomendados
                recomendaciones = response.json()
                productos_recomendados_ids = recomendaciones.get("suggested", [])
                
                # Si no hay recomendaciones, devolver respuesta vacía
                if not productos_recomendados_ids:
                    return Response(
                        {"mensaje": "No hay recomendaciones disponibles para estos productos."}, 
                        status=status.HTTP_200_OK
                    )
                
                # Obtener los detalles de los productos recomendados
                from productos.models import Producto
                from productos.serializers import ProductoSerializer
                
                productos_recomendados = Producto.objects.filter(
                    id__in=productos_recomendados_ids,
                    is_active=True
                )
                
                # Serializar los productos recomendados
                serializer = ProductoSerializer(productos_recomendados, many=True)
                
                # Devolver la respuesta con las recomendaciones
                return Response({
                    "productos_carrito": producto_ids,
                    "recomendaciones": serializer.data
                }, status=status.HTTP_200_OK)
                
            except requests.RequestException as e:
                # Manejar errores de conexión con el microservicio
                return Response(
                    {"error": f"Error al conectar con el servicio de recomendaciones: {str(e)}"}, 
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
                
        except Exception as e:
            # Manejar cualquier otro error
            return Response(
                {"error": f"Error al procesar la solicitud: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DetalleCarritoViewSet(viewsets.ModelViewSet):
    queryset = DetalleCarrito.objects.all()
    serializer_class = DetalleCarritoSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(responses={200: detalle_carrito_response})
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(responses={200: detalle_carrito_response})
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
        
    @swagger_auto_schema(request_body=detalle_carrito_request, responses={201: detalle_carrito_response})
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(
        request_body=serializers.Serializer({
            'cantidad': serializers.IntegerField(help_text='Nueva cantidad del producto (total deseado, no incremento)')
        }),
        responses={200: detalle_carrito_response}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        request_body=serializers.Serializer({
            'cantidad': serializers.IntegerField(help_text='Nueva cantidad del producto (total deseado, no incremento)')
        }),
        responses={200: detalle_carrito_response}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def get_queryset(self):
        # Manejar el caso de Swagger cuando no hay usuario autenticado
        if not self.request.user.is_authenticated:
            return DetalleCarrito.objects.none()
        return DetalleCarrito.objects.filter(
            carrito__usuario=self.request.user, 
            carrito__activo=True,
            is_active=True
        )

    def perform_create(self, serializer):
        carrito, _ = Carrito.objects.get_or_create(usuario=self.request.user, activo=True)
        serializer.save(carrito=carrito)
    
    @swagger_auto_schema(responses={200: '{"mensaje": "Producto eliminado del carrito exitosamente."}'})
    @action(detail=True, methods=['delete'], url_path='eliminar-producto')
    def eliminar_producto(self, request, pk=None):
        """
        Elimina lógicamente un producto del carrito sin importar la cantidad.
        """
        try:
            detalle = self.get_object()
            
            # Verificar que el detalle pertenece al usuario actual
            if detalle.carrito.usuario != request.user:
                return Response(
                    {"error": "No tiene permiso para modificar este carrito"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Guardar datos para la respuesta
            producto_nombre = detalle.producto.nombre
            
            # Eliminación lógica
            detalle.is_active = False
            detalle.save()
            
            return Response(
                {"mensaje": f"Producto '{producto_nombre}' eliminado del carrito exitosamente."}, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Error al eliminar el producto: {str(e)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @swagger_auto_schema(
        request_body=serializers.Serializer({
            'cantidad': serializers.IntegerField(help_text='Cantidad a reducir')
        }),
        responses={200: '{"mensaje": "Cantidad reducida exitosamente.", "cantidad_actual": 5}'},
        deprecated=True
    )
    @action(detail=True, methods=['patch'], url_path='reducir-cantidad')
    def reducir_cantidad(self, request, pk=None):
        """
        DEPRECATED: Se recomienda usar PATCH /detalle-carrito/{id}/ con la nueva cantidad total deseada.
        
        Reduce la cantidad de un producto en el carrito por la cantidad especificada.
        Si la cantidad resultante es 0 o menos, desactiva el producto del carrito.
        """
        try:
            detalle = self.get_object()
            
            # Verificar que el detalle pertenece al usuario actual
            if detalle.carrito.usuario != request.user:
                return Response(
                    {"error": "No tiene permiso para modificar este carrito"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Obtener la cantidad a reducir (por defecto 1)
            cantidad_reducir = request.data.get('cantidad', 1)
            
            # Validar que la cantidad es un número positivo
            try:
                cantidad_reducir = int(cantidad_reducir)
                if cantidad_reducir <= 0:
                    return Response(
                        {"error": "La cantidad a reducir debe ser mayor que cero."}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except (ValueError, TypeError):
                return Response(
                    {"error": "La cantidad debe ser un número entero positivo."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Calcular nueva cantidad
            nueva_cantidad = detalle.cantidad - cantidad_reducir
            
            # Si la nueva cantidad es 0 o menos, desactivar el producto
            if nueva_cantidad <= 0:
                producto_nombre = detalle.producto.nombre
                detalle.is_active = False
                detalle.save()
                return Response(
                    {"mensaje": f"Producto '{producto_nombre}' eliminado del carrito por cantidad insuficiente."}, 
                    status=status.HTTP_200_OK
                )
            
            # Actualizar la cantidad
            detalle.cantidad = nueva_cantidad
            detalle.save()  # Esto recalculará el subtotal automáticamente
            
            return Response({
                "mensaje": f"Cantidad reducida exitosamente.", 
                "cantidad_actual": nueva_cantidad,
                "subtotal": str(detalle.subtotal)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error al reducir la cantidad: {str(e)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            ) 