from rest_framework.permissions import IsAuthenticated
from .permissions import TienePermisoPersonalizado

class PermisoRequeridoMixin:
    permiso_por_accion = {}

    def get_permissions(self):
        self.permission_classes = [IsAuthenticated, TienePermisoPersonalizado]
        self.permiso_requerido = self.permiso_por_accion.get(self.action)
        return [permission() for permission in self.permission_classes]
