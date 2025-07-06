from django.db import models

# Create your models here.
from django.db import models
from django.core.validators import MinValueValidator

class Categoria(models.Model):
    nombre = models.CharField(max_length=100,unique=True)
    is_active = models.BooleanField(default=True)

class Genero(models.Model):
    nombre = models.CharField(max_length=100,unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Editorial(models.Model):
    nombre = models.CharField(max_length=100,unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Autor(models.Model):
    nombre = models.CharField(max_length=100,unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=100,unique=True)
    descripcion = models.TextField()
    stock = models.IntegerField(validators=[MinValueValidator(0)])
    imagen = models.URLField(max_length=500)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    genero = models.ForeignKey(Genero, on_delete=models.SET_NULL, null=True, blank=True)
    autor = models.ForeignKey(Autor, on_delete=models.SET_NULL, null=True, blank=True)
    editorial = models.ForeignKey(Editorial, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)


    def __str__(self):
        return self.nombre


