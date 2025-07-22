from django.db import models
from django.db import transaction
from django.core.exceptions import ValidationError

# Create your models here.
from django.db import models
from django.conf import settings
from decimal import Decimal
from datetime import date
import uuid
from productos.models import Producto


class Pedido(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pedidos"
    )

    calificacion = models.IntegerField(
        null=True,
        blank=True,
        help_text="Calificación del pedido (opcional, del 1 al 5 por ejemplo)",
    )

    fecha_pedido = models.DateTimeField(
        auto_now_add=True, help_text="Fecha en que se realizó el pedido"
    )

    descuento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Descuento aplicado en porcentaje, ej: 15.00 = 15%",
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total del pedido después del descuento",
    )

    activo = models.BooleanField(default=True)

    def calcular_total(self):
        detalles = self.detalles.all()
        total_sin_descuento = sum([detalle.subtotal for detalle in self.detalles.all()])

        # Aplicar descuento según monto total
        if total_sin_descuento > 600:
            self.descuento = Decimal(25.00)
        elif total_sin_descuento > 400:
            self.descuento = Decimal(15.00)
        elif total_sin_descuento > 200:
            self.descuento = Decimal(10.00)
        else:
            self.descuento = Decimal(0.00)

        # Aplicar el descuento al total
        total_con_descuento = total_sin_descuento - (
            total_sin_descuento * (self.descuento / Decimal(100))
        )
        self.total = total_con_descuento

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Guardar primero para que existan los detalles
        self.calcular_total()

    def __str__(self):
        return f"Pedido #{self.id} - {self.usuario}"


class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido, on_delete=models.CASCADE, related_name="detalles", null=True
    )
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    # CAMPOS PARA OFERTAS MEJORADOS
    precio_original = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00, 
        help_text="Precio original del producto sin descuento",
    )
    descuento_oferta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Descuento aplicado por oferta en valor absoluto",
    )
    nombre_oferta = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Nombre de la oferta aplicada (para historial)",
    )
    # NUEVO: Fecha de la oferta para historial
    fecha_oferta_aplicada = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha en que se aplicó la oferta (para historial)",
    )

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, blank=True)

    def save(self, *args, **kwargs):
        # Guardar precio original
        self.precio_original = self.producto.precio

        # Verificar si hay oferta vigente y aplicar descuento
        if self.producto.tiene_oferta_vigente():
            from django.utils import timezone

            self.precio_unitario = self.producto.get_precio_con_descuento()
            self.descuento_oferta = self.producto.get_descuento_aplicado()
            self.nombre_oferta = self.producto.oferta.nombre
            self.fecha_oferta_aplicada = timezone.now()
        else:
            self.precio_unitario = self.producto.precio
            self.descuento_oferta = Decimal(0.00)
            self.nombre_oferta = None
            self.fecha_oferta_aplicada = None

        # Calcular subtotal con precio final (con descuento si aplica)
        self.subtotal = self.precio_unitario * self.cantidad
        super().save(*args, **kwargs)

    def get_ahorro_total_oferta(self):
        """Calcula el ahorro total por ofertas en este detalle"""
        return self.descuento_oferta * self.cantidad

    def get_subtotal_sin_oferta(self):
        """Calcula lo que habría costado sin ofertas"""
        return self.precio_original * self.cantidad

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"


class Carrito(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="carritos"
    )
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"Carrito de {self.usuario}"

    def calcular_total(self):
        """Calcula el total actual del carrito con ofertas aplicadas"""
        return sum(
            [detalle.subtotal for detalle in self.detalles.filter(is_active=True)]
        )

    def calcular_total_original(self):
        """Calcula el total que sería sin descuentos de ofertas"""
        return sum(
            [
                detalle.precio_original * detalle.cantidad
                for detalle in self.detalles.filter(is_active=True)
            ]
        )

    def calcular_ahorro_total(self):
        """Calcula cuánto se ahorra en total por ofertas"""
        return self.calcular_total_original() - self.calcular_total()

    def actualizar_precios_ofertas(self):
        """Actualiza los precios de todos los productos según ofertas vigentes"""
        detalles_activos = self.detalles.filter(is_active=True)
        for detalle in detalles_activos:
            detalle.save()  # Esto recalculará automáticamente los precios
        return detalles_activos.count()

    def convertir_a_pedido(self):
        # Obtener solo detalles activos
        detalles_activos = self.detalles.filter(is_active=True)

        # Verificar que haya productos en el carrito
        if not detalles_activos.exists():
            raise ValidationError("No se puede crear un pedido sin productos")

        # Actualizar precios antes de convertir (por si cambiaron las ofertas)
        self.actualizar_precios_ofertas()

        # Usar transacción para garantizar la integridad
        with transaction.atomic():
            # Verificar stock de todos los productos
            for detalle in detalles_activos:
                if detalle.producto.stock < detalle.cantidad:
                    raise ValidationError(
                        f"No hay suficiente stock para '{detalle.producto.nombre}'. Stock actual: {detalle.producto.stock}"
                    )

            pedido = Pedido.objects.create(
                usuario=self.usuario,
                total=self.calcular_total(),
                descuento=0.00,  # Se calculará después
                activo=True,
            )

            # Transferir productos y actualizar stock
            for detalle in detalles_activos:
                # Disminuir stock
                producto = detalle.producto
                producto.stock -= detalle.cantidad
                producto.save()

                # Crear detalle de pedido con los mismos precios del carrito
                DetallePedido.objects.create(
                    pedido=pedido,
                    producto=producto,
                    cantidad=detalle.cantidad,
                    precio_unitario=detalle.precio_unitario,
                    precio_original=detalle.precio_original,
                    descuento_oferta=detalle.descuento_oferta,
                    nombre_oferta=detalle.nombre_oferta,
                    fecha_oferta_aplicada=detalle.fecha_oferta_aplicada,
                    subtotal=detalle.subtotal,
                )

            pedido.calcular_total()  # Calcular el descuento correcto
            pedido.save()

            self.activo = False  # Desactivar el carrito
            self.save()

        return pedido


class DetalleCarrito(models.Model):
    carrito = models.ForeignKey(
        Carrito, on_delete=models.CASCADE, related_name="detalles"
    )
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    # CAMPOS PARA OFERTAS MEJORADOS
    precio_original = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00, 
        help_text="Precio original del producto sin descuento",
    )
    descuento_oferta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Descuento aplicado por oferta en valor absoluto",
    )
    nombre_oferta = models.CharField(
        max_length=100, blank=True, null=True, help_text="Nombre de la oferta aplicada"
    )
    # NUEVO: Fecha de cuando se aplicó la oferta
    fecha_oferta_aplicada = models.DateTimeField(
        null=True, blank=True, help_text="Fecha en que se detectó y aplicó la oferta"
    )

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Guardar precio original
        self.precio_original = self.producto.precio

        # Verificar si hay oferta vigente y aplicar descuento automáticamente
        if self.producto.tiene_oferta_vigente():
            from django.utils import timezone

            self.precio_unitario = self.producto.get_precio_con_descuento()
            self.descuento_oferta = self.producto.get_descuento_aplicado()
            self.nombre_oferta = self.producto.oferta.nombre
            self.fecha_oferta_aplicada = timezone.now()
        else:
            self.precio_unitario = self.producto.precio
            self.descuento_oferta = Decimal(0.00)
            self.nombre_oferta = None
            self.fecha_oferta_aplicada = None

        # Calcular subtotal con precio final (con descuento si aplica)
        self.subtotal = self.precio_unitario * self.cantidad
        super().save(*args, **kwargs)

    def actualizar_precios(self):
        """Método para actualizar precios cuando cambien las ofertas"""
        self.save()  # Esto recalculará automáticamente los precios

    def get_ahorro_total_oferta(self):
        """Calcula el ahorro total por ofertas en este detalle"""
        return self.descuento_oferta * self.cantidad

    def get_subtotal_sin_oferta(self):
        """Calcula lo que habría costado sin ofertas"""
        return self.precio_original * self.cantidad

    def tiene_oferta_aplicada(self):
        """Verifica si este detalle tiene una oferta aplicada"""
        return self.descuento_oferta > 0 and self.nombre_oferta is not None

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"
