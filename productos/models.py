from django.db import models
from django.core.validators import MinValueValidator


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)


class Genero(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Editorial(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Autor(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Oferta(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    descuento = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Descuento en valor absoluto (ejemplo: 5.50 para descontar $5.50)",
    )
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-fecha_inicio"]

    def __str__(self):
        return f"{self.nombre} - Descuento: ${self.descuento}"

    def is_vigente(self):
        """Verifica si la oferta está vigente en la fecha actual"""
        from django.utils import timezone

        now = timezone.now()
        return self.is_active and self.fecha_inicio <= now <= self.fecha_fin


class Producto(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField()
    stock = models.IntegerField(validators=[MinValueValidator(0)])
    imagen = models.URLField(max_length=500)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    categoria = models.ForeignKey(
        Categoria, on_delete=models.SET_NULL, null=True, blank=True
    )
    genero = models.ForeignKey(Genero, on_delete=models.SET_NULL, null=True, blank=True)
    autor = models.ForeignKey(Autor, on_delete=models.SET_NULL, null=True, blank=True)
    editorial = models.ForeignKey(
        Editorial, on_delete=models.SET_NULL, null=True, blank=True
    )
    oferta = models.ForeignKey(
        Oferta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="productos",
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    def get_precio_con_descuento(self):
        """Calcula el precio con descuento si tiene oferta vigente"""
        if self.oferta and self.oferta.is_vigente():
            precio_descuento = self.precio - self.oferta.descuento
            # Asegurar que el precio no sea negativo
            return max(precio_descuento, 0)
        return self.precio

    def get_descuento_aplicado(self):
        """Retorna el descuento aplicado o 0 si no hay oferta vigente"""
        if self.oferta and self.oferta.is_vigente():
            return min(
                self.oferta.descuento, self.precio
            )  # No puede descontar más que el precio
        return 0

    def tiene_oferta_vigente(self):
        """Verifica si el producto tiene una oferta vigente"""
        return self.oferta and self.oferta.is_vigente()
