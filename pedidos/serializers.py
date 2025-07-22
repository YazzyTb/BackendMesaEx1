from rest_framework import serializers
from .models import Pedido, DetallePedido, Producto
from .models import Carrito, DetalleCarrito
from productos.serializers import ProductoSerializer
from datetime import date, timedelta
import uuid
from django.db import transaction


class DetallePedidoSerializer(serializers.ModelSerializer):
    # Incluir el objeto completo del producto
    producto = ProductoSerializer(read_only=True)

    # Campo para escritura (solo ID)
    producto_id = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.all(), source="producto", write_only=True
    )

    # Campos calculados para mostrar información de ofertas
    ahorro_por_oferta = serializers.SerializerMethodField()
    subtotal_original = serializers.SerializerMethodField()
    tiene_oferta_aplicada = serializers.SerializerMethodField()

    class Meta:
        model = DetallePedido
        fields = [
            "id",
            "pedido",
            "producto",
            "producto_id",
            "cantidad",
            "precio_unitario",
            "precio_original",
            "descuento_oferta",
            "nombre_oferta",
            "fecha_oferta_aplicada",
            "subtotal",
            "ahorro_por_oferta",
            "subtotal_original",
            "tiene_oferta_aplicada",
        ]

    def get_ahorro_por_oferta(self, obj):
        """Calcula el ahorro total por la oferta en este detalle"""
        return str(obj.get_ahorro_total_oferta())

    def get_subtotal_original(self, obj):
        """Calcula lo que habría sido el subtotal sin descuento"""
        return str(obj.get_subtotal_sin_oferta())

    def get_tiene_oferta_aplicada(self, obj):
        """Indica si este detalle tiene oferta aplicada"""
        return obj.descuento_oferta > 0

    def create(self, validated_data):
        producto = validated_data["producto"]
        cantidad = validated_data["cantidad"]

        # Verificar stock disponible
        if producto.stock < cantidad:
            raise serializers.ValidationError(
                f"No hay suficiente stock para el producto '{producto.nombre}'. Stock actual: {producto.stock}"
            )

        # Descontar stock
        producto.stock -= cantidad
        producto.save()

        # Los precios se calculan automáticamente en el save() del modelo
        # incluyendo la detección automática de ofertas
        detalle = DetallePedido.objects.create(
            producto=producto,
            cantidad=cantidad,
            **{
                k: v
                for k, v in validated_data.items()
                if k not in ["producto", "cantidad"]
            },
        )

        return detalle


class PedidoSerializer(serializers.ModelSerializer):
    # Incluir detalles en la respuesta (tanto para lectura como escritura)
    detalles = DetallePedidoSerializer(many=True, required=False)

    # Campos calculados para información adicional
    total_original = serializers.SerializerMethodField()
    ahorro_por_ofertas = serializers.SerializerMethodField()
    cantidad_productos = serializers.SerializerMethodField()
    resumen_ofertas = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = [
            "id",
            "usuario",
            "detalles",
            "descuento",
            "total",
            "fecha_pedido",
            "calificacion",
            "activo",
            "total_original",
            "ahorro_por_ofertas",
            "cantidad_productos",
            "resumen_ofertas",
        ]
        read_only_fields = ["id", "fecha_pedido"]

    def get_total_original(self, obj):
        """Calcula lo que habría sido el total sin ofertas de productos"""
        total_sin_ofertas = sum(
            [detalle.get_subtotal_sin_oferta() for detalle in obj.detalles.all()]
        )
        return str(total_sin_ofertas)

    def get_ahorro_por_ofertas(self, obj):
        """Calcula el ahorro total por ofertas de productos"""
        ahorro_total = sum(
            [detalle.get_ahorro_total_oferta() for detalle in obj.detalles.all()]
        )
        return str(ahorro_total)

    def get_cantidad_productos(self, obj):
        """Cuenta la cantidad total de productos en el pedido"""
        return sum([detalle.cantidad for detalle in obj.detalles.all()])

    def get_resumen_ofertas(self, obj):
        """Proporciona un resumen de las ofertas aplicadas"""
        detalles_con_oferta = [d for d in obj.detalles.all() if d.descuento_oferta > 0]
        ofertas_aplicadas = {}

        for detalle in detalles_con_oferta:
            nombre_oferta = detalle.nombre_oferta
            if nombre_oferta not in ofertas_aplicadas:
                ofertas_aplicadas[nombre_oferta] = {
                    "productos_count": 0,
                    "ahorro_total": 0,
                    "descuento_unitario": str(detalle.descuento_oferta),
                }
            ofertas_aplicadas[nombre_oferta]["productos_count"] += 1
            ofertas_aplicadas[nombre_oferta]["ahorro_total"] += float(
                detalle.get_ahorro_total_oferta()
            )

        # Convertir ahorros a string
        for oferta in ofertas_aplicadas.values():
            oferta["ahorro_total"] = str(oferta["ahorro_total"])

        return {
            "productos_con_oferta": len(detalles_con_oferta),
            "productos_sin_oferta": len(obj.detalles.all()) - len(detalles_con_oferta),
            "ofertas_aplicadas": ofertas_aplicadas,
            "ahorro_total": self.get_ahorro_por_ofertas(obj),
        }

    def create(self, validated_data):
        detalles_data = validated_data.pop("detalles", [])
        pedido = Pedido.objects.create(**validated_data)

        for detalle_data in detalles_data:
            DetallePedido.objects.create(pedido=pedido, **detalle_data)

        pedido.calcular_total()  # Calcula el total y aplica el descuento

        return pedido


class DetalleCarritoSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)
    producto_id = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.all(), source="producto", write_only=True
    )

    # Campos calculados para mostrar información de ofertas
    ahorro_por_oferta = serializers.SerializerMethodField()
    subtotal_original = serializers.SerializerMethodField()
    tiene_oferta = serializers.SerializerMethodField()
    # NUEVO: Información sobre la vigencia de la oferta
    oferta_vigente = serializers.SerializerMethodField()

    class Meta:
        model = DetalleCarrito
        fields = [
            "id",
            "producto",
            "producto_id",
            "cantidad",
            "precio_unitario",
            "precio_original",
            "descuento_oferta",
            "nombre_oferta",
            "fecha_oferta_aplicada",
            "subtotal",
            "ahorro_por_oferta",
            "subtotal_original",
            "tiene_oferta",
            "oferta_vigente",
        ]
        read_only_fields = [
            "precio_unitario",
            "precio_original",
            "descuento_oferta",
            "nombre_oferta",
            "fecha_oferta_aplicada",
            "subtotal",
        ]

    def get_ahorro_por_oferta(self, obj):
        """Calcula el ahorro total por la oferta en este detalle"""
        return str(obj.get_ahorro_total_oferta())

    def get_subtotal_original(self, obj):
        """Calcula lo que habría sido el subtotal sin descuento"""
        return str(obj.get_subtotal_sin_oferta())

    def get_tiene_oferta(self, obj):
        """Indica si el producto tiene oferta aplicada"""
        return obj.tiene_oferta_aplicada()

    def get_oferta_vigente(self, obj):
        """Verifica si la oferta aún está vigente"""
        if obj.producto.tiene_oferta_vigente():
            return {
                "vigente": True,
                "oferta_actual": obj.producto.oferta.nombre,
                "descuento_actual": str(obj.producto.get_descuento_aplicado()),
                "coincide_con_carrito": obj.nombre_oferta == obj.producto.oferta.nombre,
            }
        elif obj.tiene_oferta_aplicada():
            return {
                "vigente": False,
                "oferta_en_carrito": obj.nombre_oferta,
                "nota": "La oferta ya no está vigente",
            }
        return {"vigente": False, "nota": "Sin oferta aplicada"}

    def validate_cantidad(self, value):
        """
        Verificar que la cantidad sea mayor que cero.
        """
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor que cero.")
        return value

    def validate(self, data):
        """
        Verificar que haya suficiente stock para el producto.
        """
        cantidad = data.get("cantidad")
        producto = data.get("producto")

        # Si no se proporciona producto, usar el producto actual del instance
        if not producto and self.instance:
            producto = self.instance.producto

        # Verificar que tenemos un producto válido
        if not producto:
            raise serializers.ValidationError(
                "No se pudo determinar el producto para validar el stock."
            )

        # Verificar stock disponible
        if producto.stock < cantidad:
            raise serializers.ValidationError(
                f"No hay suficiente stock para el producto '{producto.nombre}'. Stock actual: {producto.stock}"
            )

        return data

    def create(self, validated_data):
        carrito = validated_data.get("carrito")
        producto = validated_data.get("producto")
        cantidad = validated_data.get("cantidad")

        # Buscar si el producto ya existe en el carrito
        with transaction.atomic():
            detalle_existente = DetalleCarrito.objects.filter(
                carrito=carrito, producto=producto, is_active=True
            ).first()

            if detalle_existente:
                # Verificar que haya suficiente stock para la cantidad aumentada
                cantidad_total = detalle_existente.cantidad + cantidad
                if producto.stock < cantidad_total:
                    raise serializers.ValidationError(
                        f"No hay suficiente stock para el producto '{producto.nombre}'. "
                        f"Stock actual: {producto.stock}, cantidad en carrito: {detalle_existente.cantidad}"
                    )

                # Actualizar cantidad del item existente
                detalle_existente.cantidad = cantidad_total
                detalle_existente.save()  # Esto recalculará automáticamente los precios y ofertas
                return detalle_existente
            else:
                # Crear nuevo detalle de carrito - save() calculará automáticamente precios y ofertas
                return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Actualiza la cantidad de un producto en el carrito.
        Si la cantidad nueva es 0, desactiva el producto en lugar de eliminarlo.
        """
        nueva_cantidad = validated_data.get("cantidad", instance.cantidad)

        # Si la cantidad es 0, desactivar el producto
        if nueva_cantidad == 0:
            instance.is_active = False
            instance.save()
            return instance

        # Verificar stock disponible usando el producto actual
        if instance.producto.stock < nueva_cantidad:
            raise serializers.ValidationError(
                f"No hay suficiente stock para el producto '{instance.producto.nombre}'. Stock actual: {instance.producto.stock}"
            )

        # Actualizar cantidad y recalcular precios y ofertas
        instance.cantidad = nueva_cantidad
        instance.save()  # Esto recalculará automáticamente precios, ofertas y subtotal

        return instance


class CarritoSerializer(serializers.ModelSerializer):
    detalles = DetalleCarritoSerializer(many=True, read_only=True)

    # Campos calculados para información del carrito
    total_original = serializers.SerializerMethodField()
    ahorro_por_ofertas = serializers.SerializerMethodField()
    cantidad_productos = serializers.SerializerMethodField()
    cantidad_items = serializers.SerializerMethodField()
    resumen_ofertas = serializers.SerializerMethodField()

    class Meta:
        model = Carrito
        fields = [
            "id",
            "usuario",
            "activo",
            "detalles",
            "total_original",
            "ahorro_por_ofertas",
            "cantidad_productos",
            "cantidad_items",
            "resumen_ofertas",
        ]
        read_only_fields = ["usuario"]

    def get_total_original(self, obj):
        """Calcula lo que sería el total sin descuentos por ofertas"""
        return str(obj.calcular_total_original())

    def get_ahorro_por_ofertas(self, obj):
        """Calcula cuánto se ahorra por ofertas"""
        return str(obj.calcular_ahorro_total())

    def get_cantidad_productos(self, obj):
        """Cuenta la cantidad total de productos en el carrito"""
        return sum(
            [detalle.cantidad for detalle in obj.detalles.filter(is_active=True)]
        )

    def get_cantidad_items(self, obj):
        """Cuenta cuántos tipos de productos diferentes hay en el carrito"""
        return obj.detalles.filter(is_active=True).count()

    def get_resumen_ofertas(self, obj):
        """Proporciona un resumen detallado de las ofertas en el carrito"""
        detalles_activos = obj.detalles.filter(is_active=True)
        detalles_con_oferta = [d for d in detalles_activos if d.tiene_oferta_aplicada()]

        ofertas_aplicadas = {}
        ofertas_expiradas = []

        for detalle in detalles_con_oferta:
            # Verificar si la oferta aún está vigente
            if (
                detalle.producto.tiene_oferta_vigente()
                and detalle.nombre_oferta == detalle.producto.oferta.nombre
            ):
                # Oferta vigente
                nombre_oferta = detalle.nombre_oferta
                if nombre_oferta not in ofertas_aplicadas:
                    ofertas_aplicadas[nombre_oferta] = {
                        "productos_count": 0,
                        "ahorro_total": 0,
                        "descuento_unitario": str(detalle.descuento_oferta),
                        "vigente": True,
                    }
                ofertas_aplicadas[nombre_oferta]["productos_count"] += 1
                ofertas_aplicadas[nombre_oferta]["ahorro_total"] += float(
                    detalle.get_ahorro_total_oferta()
                )
            else:
                # Oferta expirada o cambiada
                ofertas_expiradas.append(
                    {
                        "producto": detalle.producto.nombre,
                        "oferta_anterior": detalle.nombre_oferta,
                        "descuento_anterior": str(detalle.descuento_oferta),
                        "nota": "Oferta ya no vigente",
                    }
                )

        # Convertir ahorros a string
        for oferta in ofertas_aplicadas.values():
            oferta["ahorro_total"] = str(oferta["ahorro_total"])

        return {
            "productos_con_oferta_vigente": len(
                [d for d in detalles_con_oferta if d.producto.tiene_oferta_vigente()]
            ),
            "productos_sin_oferta": len(detalles_activos) - len(detalles_con_oferta),
            "ofertas_vigentes": ofertas_aplicadas,
            "ofertas_expiradas": ofertas_expiradas,
            "ahorro_total": self.get_ahorro_por_ofertas(obj),
            "total_con_ofertas": str(obj.calcular_total()),
            "total_sin_ofertas": str(obj.calcular_total_original()),
        }
