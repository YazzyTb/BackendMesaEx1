from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import Producto, Categoria, Autor, Genero, Editorial
from productos.serializers import (
    ProductoSerializer,
    CategoriaSerializer,
    AutorSerializer,
    GeneroSerializer,
    EditorialSerializer,
)

from usuarios.permissions import TienePermisoPersonalizado


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [TienePermisoPersonalizado]

    permiso_por_accion = {
        'list': 'ver_productos',
        'create': 'crear_productos',
        'update': 'editar_productos',
        'partial_update': 'editar_productos',
        'destroy': 'eliminar_productos',
    }

    def get_queryset(self):
        return Producto.objects.filter(is_active=True)

class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [TienePermisoPersonalizado]

    permiso_por_accion = {
        'list': 'ver_categorias',
        'create': 'crear_categorias',
        'update': 'editar_categorias',
        'partial_update': 'editar_categorias',
        'destroy': 'eliminar_categorias',
    }




class AutorViewSet(viewsets.ModelViewSet):
        queryset = Autor.objects.all()
        serializer_class = AutorSerializer
        permission_classes = [TienePermisoPersonalizado]

        permiso_por_accion = {
            'list': 'ver_autores',
            'create': 'crear_autores',
            'update': 'editar_autores',
            'partial_update': 'editar_autores',
            'destroy': 'eliminar_autores',
        }


class GeneroViewSet(viewsets.ModelViewSet):
    queryset = Genero.objects.all()
    serializer_class = GeneroSerializer
    permission_classes = [TienePermisoPersonalizado]

    permiso_por_accion = {
        'list': 'ver_generos',
        'create': 'crear_generos',
        'update': 'editar_generos',
        'partial_update': 'editar_generos',
        'destroy': 'eliminar_generos',
    }


class EditorialViewSet(viewsets.ModelViewSet):
    queryset = Editorial.objects.all()
    serializer_class = EditorialSerializer
    permission_classes = [TienePermisoPersonalizado]

    permiso_por_accion = {
        'list': 'ver_editoriales',
        'create': 'crear_editoriales',
        'update': 'editar_editoriales',
        'partial_update': 'editar_editoriales',
        'destroy': 'eliminar_editoriales',
    }
