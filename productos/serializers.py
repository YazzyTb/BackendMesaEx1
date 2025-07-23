from rest_framework import serializers
from .models import Producto, Categoria, Autor, Genero, Editorial, Oferta
from rest_framework.validators import UniqueTogetherValidator
from django.utils import timezone


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = "__all__"

    def validate_nombre(self, value):
        categoria_id = self.instance.id if self.instance else None
        if (
            Categoria.objects.filter(nombre__iexact=value)
            .exclude(id=categoria_id)
            .exists()
        ):
            raise serializers.ValidationError("Ya existe una categoría con ese nombre.")
        return value


class AutorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Autor
        fields = "__all__"

    def validate_nombre(self, value):
        # Si estamos actualizando, ignoramos el autor actual en la búsqueda
        autor_id = self.instance.id if self.instance else None
        if Autor.objects.filter(nombre__iexact=value).exclude(id=autor_id).exists():
            raise serializers.ValidationError(
                "Este nombre de autor ya está registrado."
            )
        return value


class GeneroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genero
        fields = "__all__"

    def validate_nombre(self, value):
        genero_id = self.instance.id if self.instance else None
        if Genero.objects.filter(nombre__iexact=value).exclude(id=genero_id).exists():
            raise serializers.ValidationError("Este género ya existe.")
        return value


class EditorialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Editorial
        fields = "__all__"

    def validate_nombre(self, value):
        editorial_id = self.instance.id if self.instance else None
        if (
            Editorial.objects.filter(nombre__iexact=value)
            .exclude(id=editorial_id)
            .exists()
        ):
            raise serializers.ValidationError("Esta editorial ya está registrada.")
        return value


class OfertaSerializer(serializers.ModelSerializer):
    productos_count = serializers.SerializerMethodField()
    is_vigente = serializers.SerializerMethodField()

    class Meta:
        model = Oferta
        fields = [
            "id",
            "nombre",
            "descripcion",
            "descuento",
            "fecha_inicio",
            "fecha_fin",
            "is_active",
            "productos_count",
            "is_vigente",
        ]

    def get_productos_count(self, obj):
        """Cuenta cuántos productos están asociados a esta oferta"""
        return obj.productos.filter(is_active=True).count()

    def get_is_vigente(self, obj):
        """Indica si la oferta está vigente actualmente"""
        return obj.is_vigente()

    def validate_nombre(self, value):
        """Valida que el nombre de la oferta sea único"""
        oferta_id = self.instance.id if self.instance else None
        if Oferta.objects.filter(nombre__iexact=value).exclude(id=oferta_id).exists():
            raise serializers.ValidationError("Ya existe una oferta con ese nombre.")
        return value

    def validate(self, data):
        """Validaciones personalizadas para la oferta"""
        fecha_inicio = data.get("fecha_inicio")
        fecha_fin = data.get("fecha_fin")

        # Validar que la fecha de fin sea posterior a la fecha de inicio
        if fecha_inicio and fecha_fin and fecha_fin <= fecha_inicio:
            raise serializers.ValidationError(
                "La fecha de fin debe ser posterior a la fecha de inicio."
            )

        # Validar que el descuento sea positivo
        descuento = data.get("descuento")
        if descuento is not None and descuento < 0:
            raise serializers.ValidationError("El descuento no puede ser negativo.")

        return data


class ProductoSerializer(serializers.ModelSerializer):
    # Incluir los objetos completos para las relaciones
    categoria = CategoriaSerializer(read_only=True)
    genero = GeneroSerializer(read_only=True)
    autor = AutorSerializer(read_only=True)
    editorial = EditorialSerializer(read_only=True)
    oferta = OfertaSerializer(read_only=True)

    # Campos para escritura (solo IDs)
    categoria_id = serializers.PrimaryKeyRelatedField(
        queryset=Categoria.objects.all(), source="categoria", write_only=True
    )
    genero_id = serializers.PrimaryKeyRelatedField(
        queryset=Genero.objects.all(),
        source="genero",
        write_only=True,
        required=False,
        allow_null=True,
    )
    autor_id = serializers.PrimaryKeyRelatedField(
        queryset=Autor.objects.all(),
        source="autor",
        write_only=True,
        required=False,
        allow_null=True,
    )
    editorial_id = serializers.PrimaryKeyRelatedField(
        queryset=Editorial.objects.all(),
        source="editorial",
        write_only=True,
        required=False,
        allow_null=True,
    )
    oferta_id = serializers.PrimaryKeyRelatedField(
        queryset=Oferta.objects.all(),
        source="oferta",
        write_only=True,
        required=False,
        allow_null=True,
    )

    # Campos calculados para mostrar precios y descuentos
    precio_con_descuento = serializers.SerializerMethodField()
    descuento_aplicado = serializers.SerializerMethodField()
    tiene_oferta_vigente = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            "id",
            "nombre",
            "descripcion",
            "stock",
            "imagen",
            "precio",
            "categoria",
            "genero",
            "autor",
            "editorial",
            "oferta",
            "categoria_id",
            "genero_id",
            "autor_id",
            "editorial_id",
            "oferta_id",
            "is_active",
            "precio_con_descuento",
            "descuento_aplicado",
            "tiene_oferta_vigente",
        ]

    def get_precio_con_descuento(self, obj):
        """Calcula y retorna el precio con descuento aplicado"""
        return str(obj.get_precio_con_descuento())

    def get_descuento_aplicado(self, obj):
        """Retorna el descuento aplicado"""
        return str(obj.get_descuento_aplicado())

    def get_tiene_oferta_vigente(self, obj):
        """Indica si el producto tiene una oferta vigente"""
        return obj.tiene_oferta_vigente()

    def validate(self, data):
        instance = self.instance
        # Validamos en base al nombre de la categoría
        categoria_obj = data.get("categoria")
        if not categoria_obj:
            raise serializers.ValidationError(
                {"categoria": "La categoría es requerida."}
            )

        nombre_categoria = categoria_obj.nombre.lower()

        # Si es "accesorios", no deben enviarse esos campos
        if nombre_categoria.lower() == "accesorios":
            if data.get("genero") or data.get("autor") or data.get("editorial"):
                raise serializers.ValidationError(
                    "Los campos 'genero', 'autor' y 'editorial' no deben enviarse para accesorios."
                )

        return data


class OfertaDetalladaSerializer(OfertaSerializer):
    """Serializer extendido que incluye los productos asociados a la oferta"""

    productos = ProductoSerializer(many=True, read_only=True)

    class Meta(OfertaSerializer.Meta):
        fields = OfertaSerializer.Meta.fields + ["productos"]
