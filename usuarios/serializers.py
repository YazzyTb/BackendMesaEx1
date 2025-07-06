from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Rol, Permiso

#maneja el json
class PermisoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permiso
        fields = ['id', 'nombre']

    def validate_nombre(self, value):
        permiso_id = self.instance.id if self.instance else None
        if Permiso.objects.filter(nombre__iexact=value).exclude(id=permiso_id).exists():
            raise serializers.ValidationError("Este permiso ya está registrado.")
        return value


class RolSerializer(serializers.ModelSerializer):
    permisos = PermisoSerializer(many=True, read_only=True)
    permisos_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Permiso.objects.all(), write_only=True, source='permisos'
    )

    class Meta:
        model = Rol
        fields = ['id', 'nombre', 'permisos', 'permisos_ids']

    def validate_nombre(self, value):
        rol_id = self.instance.id if self.instance else None
        if Rol.objects.filter(nombre__iexact=value).exclude(id=rol_id).exists():
            raise serializers.ValidationError("Este rol ya existe.")
        return value


# Obtén el modelo de usuario (con tu configuración personalizada)
Usuario = get_user_model()


class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True)  # Esto oculta la contraseña en las respuestas, pero permite enviarla

    rol = serializers.PrimaryKeyRelatedField(queryset=Rol.objects.all(), allow_null=True, required=False)

    class Meta:
        model = Usuario
        fields = ['id', 'email', 'nombre_completo', 'telefono', 'direccion',
                  'password','rol']  # Excluimos 'username' y mantenemos el 'email'
        extra_kwargs = {'password': {'write_only': True}}  # La contraseña solo se utilizará en la creación del usuario

    def validate_email(self, value):
        usuario_id = self.instance.id if self.instance else None
        if Usuario.objects.filter(email__iexact=value).exclude(id=usuario_id).exists():
            raise serializers.ValidationError("Este correo ya está registrado.")
        return value

    def validate_nombre_completo(self, value):
        usuario_id = self.instance.id if self.instance else None
        if Usuario.objects.filter(nombre_completo__iexact=value).exclude(id=usuario_id).exists():
            raise serializers.ValidationError("Este nombre ya está registrado.")
        return value

    def create(self, validated_data):
        """Crea un usuario con contraseña encriptada"""
        # Extraemos la contraseña del diccionario de datos validados
        password = validated_data.pop('password')

        # Creamos el usuario con los datos validados (sin la contraseña aún)
        usuario = Usuario(**validated_data)

        # Encriptamos la contraseña
        usuario.set_password(password)

        # Guardamos el usuario en la base de datos
        usuario.save()

        return usuario

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance