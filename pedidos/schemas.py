from drf_yasg import openapi

# Esquemas para el carrito
carrito_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
        'usuario': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
        'activo': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
        'detalles': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                    'producto': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                            'nombre': openapi.Schema(type=openapi.TYPE_STRING, example="Cien años de soledad"),
                            'precio': openapi.Schema(type=openapi.TYPE_STRING, example="25.99"),
                            'stock': openapi.Schema(type=openapi.TYPE_INTEGER, example=15),
                        }
                    ),
                    'cantidad': openapi.Schema(type=openapi.TYPE_INTEGER, example=2),
                    'precio_unitario': openapi.Schema(type=openapi.TYPE_STRING, example="25.99"),
                    'subtotal': openapi.Schema(type=openapi.TYPE_STRING, example="51.98"),
                }
            )
        )
    }
)

# Esquema para respuesta de carrito activo
carrito_response = openapi.Response(
    description="Carrito con sus detalles",
    schema=carrito_schema
)

# Esquema para solicitud de creación de carrito
carrito_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'activo': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
    }
)

# Esquema para detalle de carrito
detalle_carrito_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
        'producto': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                'nombre': openapi.Schema(type=openapi.TYPE_STRING, example="Cien años de soledad"),
                'precio': openapi.Schema(type=openapi.TYPE_STRING, example="25.99"),
                'stock': openapi.Schema(type=openapi.TYPE_INTEGER, example=15),
            }
        ),
        'cantidad': openapi.Schema(type=openapi.TYPE_INTEGER, example=2),
        'precio_unitario': openapi.Schema(type=openapi.TYPE_STRING, example="25.99"),
        'subtotal': openapi.Schema(type=openapi.TYPE_STRING, example="51.98"),
    }
)

# Esquema para respuesta de detalle de carrito
detalle_carrito_response = openapi.Response(
    description="Detalle de carrito",
    schema=detalle_carrito_schema
)

# Esquema para solicitud de creación de detalle de carrito
detalle_carrito_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['producto_id', 'cantidad'],
    properties={
        'producto_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
        'cantidad': openapi.Schema(type=openapi.TYPE_INTEGER, example=2),
    }
)

# Esquema para respuesta de conversión a pedido
pedido_conversion_response = openapi.Response(
    description="Resultado de conversión a pedido",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'mensaje': openapi.Schema(type=openapi.TYPE_STRING, example="Carrito convertido a pedido exitosamente."),
            'pedido_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
        }
    )
) 