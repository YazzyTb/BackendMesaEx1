from rest_framework import serializers
from .models import Producto, Categoria, Autor, Genero, Editorial
from rest_framework.validators import UniqueTogetherValidator


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'

    def validate_nombre(self, value):
        categoria_id = self.instance.id if self.instance else None
        if Categoria.objects.filter(nombre__iexact=value).exclude(id=categoria_id).exists():
            raise serializers.ValidationError("Ya existe una categoría con ese nombre.")
        return value


class AutorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Autor
        fields = '__all__'

    def validate_nombre(self, value):
        # Si estamos actualizando, ignoramos el autor actual en la búsqueda
        autor_id = self.instance.id if self.instance else None
        if Autor.objects.filter(nombre__iexact=value).exclude(id=autor_id).exists():
            raise serializers.ValidationError("Este nombre de autor ya está registrado.")
        return value

class GeneroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genero
        fields = '__all__'

    def validate_nombre(self, value):
        genero_id = self.instance.id if self.instance else None
        if Genero.objects.filter(nombre__iexact=value).exclude(id=genero_id).exists():
            raise serializers.ValidationError("Este género ya existe.")
        return value


class EditorialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Editorial
        fields = '__all__'

    def validate_nombre(self, value):
        editorial_id = self.instance.id if self.instance else None
        if Editorial.objects.filter(nombre__iexact=value).exclude(id=editorial_id).exists():
            raise serializers.ValidationError("Esta editorial ya está registrada.")
        return value


class ProductoSerializer(serializers.ModelSerializer):
    # Incluir los objetos completos para las relaciones
    categoria = CategoriaSerializer(read_only=True)
    genero = GeneroSerializer(read_only=True)
    autor = AutorSerializer(read_only=True)
    editorial = EditorialSerializer(read_only=True)
    
    # Campos para escritura (solo IDs)
    categoria_id = serializers.PrimaryKeyRelatedField(
        queryset=Categoria.objects.all(), source='categoria', write_only=True
    )
    genero_id = serializers.PrimaryKeyRelatedField(
        queryset=Genero.objects.all(), source='genero', write_only=True, required=False, allow_null=True
    )
    autor_id = serializers.PrimaryKeyRelatedField(
        queryset=Autor.objects.all(), source='autor', write_only=True, required=False, allow_null=True
    )
    editorial_id = serializers.PrimaryKeyRelatedField(
        queryset=Editorial.objects.all(), source='editorial', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'descripcion', 'stock', 'imagen', 'precio', 
                 'categoria', 'genero', 'autor', 'editorial',
                 'categoria_id', 'genero_id', 'autor_id', 'editorial_id',
                 'is_active']

    def validate(self, data):
        instance = self.instance
        # Validamos en base al nombre de la categoría
        categoria_obj = data.get('categoria')
        if not categoria_obj:
            raise serializers.ValidationError({"categoria": "La categoría es requerida."})

        nombre_categoria = categoria_obj.nombre.lower()

        # Si es "accesorios", no deben enviarse esos campos
        if nombre_categoria.lower() == "accesorios":
            if data.get('genero') or data.get('autor') or data.get('editorial'):
                raise serializers.ValidationError(
                    "Los campos 'genero', 'autor' y 'editorial' no deben enviarse para accesorios.")

        return data
