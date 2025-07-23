from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Categoria, Genero, Editorial, Autor, Producto, Oferta


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["nombre"]


@admin.register(Genero)
class GeneroAdmin(admin.ModelAdmin):
    list_display = ["nombre", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["nombre"]


@admin.register(Editorial)
class EditorialAdmin(admin.ModelAdmin):
    list_display = ["nombre", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["nombre"]


@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ["nombre", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["nombre"]


@admin.register(Oferta)
class OfertaAdmin(admin.ModelAdmin):
    list_display = [
        "nombre",
        "descuento",
        "fecha_inicio",
        "fecha_fin",
        "is_active",
        "productos_count",
    ]
    list_filter = ["is_active", "fecha_inicio", "fecha_fin"]
    search_fields = ["nombre", "descripcion"]
    date_hierarchy = "fecha_inicio"

    def productos_count(self, obj):
        return obj.productos.filter(is_active=True).count()

    productos_count.short_description = "Productos en oferta"


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = [
        "nombre",
        "precio",
        "stock",
        "categoria",
        "oferta",
        "tiene_oferta_vigente",
        "is_active",
    ]
    list_filter = ["is_active", "categoria", "oferta", "autor", "editorial"]
    search_fields = ["nombre", "descripcion"]
    raw_id_fields = ["oferta"]

    def tiene_oferta_vigente(self, obj):
        return obj.tiene_oferta_vigente()

    tiene_oferta_vigente.boolean = True
    tiene_oferta_vigente.short_description = "Oferta vigente"
