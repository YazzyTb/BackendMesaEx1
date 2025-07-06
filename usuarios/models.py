from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

#aca se crean las tablas
class Rol(models.Model):
    nombre = models.CharField(max_length=100,unique=True)
    permisos = models.ManyToManyField("Permiso", related_name='roles')
    is_active = models.BooleanField(default=True)


    def __str__(self):
        return self.nombre

class Permiso(models.Model):
    nombre = models.CharField(max_length=100,unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El email debe ser proporcionado")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, password, **extra_fields)

class Usuario(AbstractBaseUser):
    email = models.EmailField(unique=True)
    nombre_completo = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20, blank=True, null=True)  # Nuevo campo
    direccion = models.TextField(blank=True, null=True)  # Nuevo campo
    password = models.CharField(max_length=255)

    rol = models.ForeignKey(Rol, on_delete=models.SET_NULL, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre_completo']

    def __str__(self):
        return self.email