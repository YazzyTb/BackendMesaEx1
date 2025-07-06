from rest_framework.permissions import BasePermission


class TienePermisoPersonalizado(BasePermission):
    def has_permission(self, request, view):
        usuario = request.user

        if not usuario.is_authenticated:
            return False

        # Aquí defines el nombre del permiso que debe tener
        permiso_requerido = getattr(view, 'permiso_requerido', None)

        if permiso_requerido is None:
            return True  # Si no se especifica un permiso, se permite por defecto

        rol = usuario.rol
        if rol is None:
            return False

        # Verificar si el rol tiene el permiso requerido
        return rol.permisos.filter(nombre=permiso_requerido).exists()
