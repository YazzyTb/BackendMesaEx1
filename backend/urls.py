from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from usuarios.views import UsuarioViewSet, LoginView, RolViewSet, PermisoViewSet

# Swagger
from rest_framework.authentication import TokenAuthentication
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configuración de rutas automáticas
router = DefaultRouter()
router.register(r"usuarios", UsuarioViewSet, basename="usuario")
router.register(r"roles", RolViewSet, basename="rol")
router.register(r"permisos", PermisoViewSet, basename="permiso")

from productos.views import (
    ProductoViewSet,
    CategoriaViewSet,
    AutorViewSet,
    GeneroViewSet,
    EditorialViewSet,
    OfertaViewSet,
)


# Registro de rutas para la app productos
router.register(r"productos", ProductoViewSet, basename="producto")
router.register(r"categorias", CategoriaViewSet, basename="categoria")
router.register(r"autores", AutorViewSet, basename="autor")
router.register(r"generos", GeneroViewSet, basename="genero")
router.register(r"editoriales", EditorialViewSet, basename="editorial")
router.register(r"ofertas", OfertaViewSet, basename="oferta")

from pedidos.views import (
    PedidoViewSet,
    DetallePedidoViewSet,
    CarritoViewSet,
    DetalleCarritoViewSet,
)


router.register(r"pedidos", PedidoViewSet, basename="pedido")
router.register(r"detalles", DetallePedidoViewSet, basename="detallepedido")
router.register(r"carrito", CarritoViewSet, basename="carrito")
router.register(r"detalle-carrito", DetalleCarritoViewSet, basename="detalle-carrito")

# NUEVA LÍNEA PARA REPORTES
from reportes.views import ReporteViewSet

router.register(r"reportes", ReporteViewSet, basename="reporte")
schema_view = get_schema_view(
    openapi.Info(
        title="API Backend SI2",
        default_version="v1",
        description="Documentación interactiva de la API",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="tucorreo@ejemplo.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=[TokenAuthentication],
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("Libreria/", include(router.urls)),
    path("Libreria/login/", LoginView.as_view(), name="login"),
    path(
        "Libreria/ml-csv/",
        PedidoViewSet.as_view({"get": "descargar_ml_csv"}),
        name="ml-csv-download",
    ),
    # Ruta adicional para aplicar oferta con ID en URL
    # Permite usar /productos/{id}/aplicar-oferta/{oferta_id}/
    re_path(
        r"^Libreria/productos/(?P<pk>[^/.]+)/aplicar-oferta/(?P<oferta_id>[^/.]+)/$",
        ProductoViewSet.as_view({"post": "aplicar_oferta"}),
        name="producto-aplicar-oferta",
    ),
    # Swagger y ReDoc
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
