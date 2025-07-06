from rest_framework import viewsets
from django.contrib.auth import get_user_model
from .serializers import UsuarioSerializer, RolSerializer, PermisoSerializer
from rest_framework.permissions import  AllowAny
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from .models import Rol, Permiso
from rest_framework.decorators import action
from rest_framework import status

##es como el service , se crea la logica del crud
Usuario = get_user_model()

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    swagger_tags = ['Usuarios']
    permiso_por_accion = {
        'list': 'ver_usuarios',
        'create': 'crear_usuarios',
        'update': 'editar_usuario',
        'partial_update': 'editar_usuario',
        'destroy': 'eliminar_usuario',
    }

    def get_permissions(self):
        # Solo en 'list' quieres permitir acceso público
        if self.action == 'list':
            return [AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        return Usuario.objects.filter(is_active=True)

    #crear un cliente
    @action(detail=False, methods=['post'], url_path='crear-cliente', permission_classes=[AllowAny])
    def crear_cliente(self, request):
        # 1. Buscar o crear el rol "cliente"
        rol_cliente, creado = Rol.objects.get_or_create(nombre='cliente')

        # 2. Copiar los datos del request
        data = request.data.copy()

        # 3. Asignar el rol al request
        data['rol'] = rol_cliente.id

        # 4. Usar el serializer para validar y crear el usuario
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    #logica para eliminar
    def destroy(self, request, *args, **kwargs):
        usuario = self.get_object()
        usuario.is_active = False  # Marcar como inactivo
        usuario.save()
        return Response({'detalle': 'Usuario desactivado correctamente.'}, status=204)


class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    swagger_tags = ['Roles']
    permiso_por_accion = {
        'list': 'ver_roles',
        'create': 'crear_roles',
        'update': 'editar_rol',
        'partial_update': 'editar_rol',
        'destroy': 'eliminar_rol',
    }

    def get_queryset(self):
        return Rol.objects.filter(is_active=True)

    def destroy(self, request, *args, **kwargs):
        rol = self.get_object()
        rol.is_active = False
        rol.save()
        return Response({'detalle': 'Rol desactivado correctamente.'}, status=204)

class PermisoViewSet(viewsets.ModelViewSet):
    queryset = Permiso.objects.all()
    serializer_class = PermisoSerializer
    swagger_tags = ['Permisos']
    permiso_por_accion = {
        'list': 'ver_permisos',
        'create': 'crear_permisos',
        'update': 'editar_permiso',
        'partial_update': 'editar_permiso',
        'destroy': 'eliminar_permiso',
    }

    def get_queryset(self):
        return Permiso.objects.filter(is_active=True)

    def destroy(self, request, *args, **kwargs):
        permiso = self.get_object()
        permiso.is_active = False
        permiso.save()
        return Response({'detalle': 'Permiso desactivado correctamente.'}, status=204)

    @action(detail=False, methods=['post'], url_path='crear-multiples')
    def crear_multiples(self, request):
        data = request.data

        # Si mandas un solo objeto, conviértelo en lista para manejar ambos casos
        if isinstance(data, dict):
            data = [data]

        serializer = PermisoSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginView(ObtainAuthToken):
    swagger_tags = ['Login']

    def post(self, request, *args, **kwargs):
        email = request.data.get('username')
        password = request.data.get('password')

        if not email or not password:
            raise AuthenticationFailed('Email y password son requeridos.')

        Usuario = get_user_model()
        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            raise AuthenticationFailed('Este correo no está registrado.')

        if not user.check_password(password):
            raise AuthenticationFailed('La contraseña es incorrecta.')

        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)

        # Usar el serializer para obtener datos completos del usuario
        from .serializers import UsuarioSerializer
        user_serializer = UsuarioSerializer(user)

        # Devolver token, user_id y datos completos del usuario
        return Response({
            'token': token.key, 
            'user_id': user.id,
            'usuario': user_serializer.data
        })
