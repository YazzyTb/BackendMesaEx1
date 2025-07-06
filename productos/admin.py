from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Categoria, Genero, Editorial, Autor, Producto

admin.site.register(Categoria)
admin.site.register(Genero)
admin.site.register(Editorial)
admin.site.register(Autor)
admin.site.register(Producto)
