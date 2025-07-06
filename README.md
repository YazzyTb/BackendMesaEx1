# API Backend - Carrito de Compras y Sistema de Pedidos
# Proyecto SI2-P1-Backend

Este es el backend del proyecto SI2-P1, desarrollado en **Django Rest Framework**.

## 📌 Requisitos
- **Python 3.13** instalado
- **pip** y **virtualenv** disponibles
- **PostgreSQL** (si el proyecto usa esta base de datos)

## 🚀 Instalación

### 1️⃣ Crear y activar el entorno virtual
```bash
# Crear el entorno virtual
python -m venv .venv

# Activar el entorno virtual
# En Windows
.venv\Scripts\activate

# En Linux/Mac
source .venv/bin/activate
```

### 2️⃣ Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3️⃣ Aplicar migraciones y ejecutar el servidor
```bash
# Aplicar migraciones a la base de datos
python manage.py migrate

# Crear un superusuario (opcional, para acceder al admin)
python manage.py createsuperuser

# Ejecutar el servidor
python manage.py runserver
```

## 📄 Documentación con Swagger
La documentación interactiva de la API está disponible en:

🔗 [http://localhost:8000/swagger/](http://localhost:8000/swagger/)

## 📌 Comandos útiles
- **Salir del entorno virtual**:
  ```bash
  deactivate
  ```
- **Actualizar dependencias y guardar cambios en `requirements.txt`**:
  ```bash
  pip freeze > requirements.txt
  ```

---
MODELO (models.py)
   ↓
SERIALIZER (serializers.py)
   ↓
VIEWSET (views.py)
   ↓
RUTAS (urls.py) → No lo vimos, pero es donde se conectan estas vistas
   ↓
CLIENTE (Angular u otro)


📅 **Fecha de última actualización**: [5/4/2025]



Este documento explica detalladamente el funcionamiento de los endpoints para gestionar el carrito de compras y los pedidos en el sistema, incluyendo su interacción entre sí y el flujo de trabajo completo.

## Índice
1. [Introducción](#introducción)
2. [Autenticación](#autenticación)
3. [Endpoints del Carrito](#endpoints-del-carrito)
4. [Endpoints de Detalles del Carrito](#endpoints-de-detalles-del-carrito)
5. [Endpoints de Pedidos](#endpoints-de-pedidos)
6. [Endpoints de Detalles de Pedidos](#endpoints-de-detalles-de-pedidos)
7. [Flujo Completo de Compra](#flujo-completo-de-compra)
8. [Reglas de Negocio](#reglas-de-negocio)
9. [Manejo de Errores](#manejo-de-errores)

## Introducción

El sistema implementa un flujo de compra en dos etapas principales:
1. **Carrito de compras**: Donde el usuario agrega productos temporalmente
2. **Pedido**: Cuando el usuario confirma la compra y se procesa el pedido

Cada usuario autenticado tiene un carrito activo al que puede agregar productos. Cuando está listo para finalizar la compra, el carrito se convierte en un pedido.

## Autenticación

Todos los endpoints relacionados con carritos y pedidos requieren autenticación mediante token.

```
POST /Libreria/login/
{
  "username": "usuario",
  "password": "contraseña"
}
```

**Respuesta**:
```
{
  "token": "a3b4c5d6..."
}
```

Este token debe incluirse en las cabeceras de todas las peticiones subsiguientes:
```
Authorization: Token a3b4c5d6...
```

## Endpoints del Carrito

### Obtener Carrito Activo
Devuelve el carrito activo del usuario autenticado, o crea uno nuevo si no existe.

```
GET /Libreria/carrito/activo/
```

**Respuesta**:
```json
{
  "id": 1,
  "usuario": 1,
  "activo": true,
  "detalles": [
    {
      "id": 1,
      "producto": {
        "id": 1,
        "nombre": "Cien años de soledad",
        "precio": "25.99",
        "stock": 10
      },
      "cantidad": 2,
      "precio_unitario": "25.99",
      "subtotal": "51.98"
    }
  ]
}
```

### Listar Todos los Carritos del Usuario
Devuelve todos los carritos del usuario autenticado (activos e inactivos).

```
GET /Libreria/carrito/
```

### Obtener Detalles de un Carrito Específico
Devuelve la información completa de un carrito específico.

```
GET /Libreria/carrito/{id}/
```

### Convertir Carrito a Pedido
Convierte el carrito activo en un pedido formal.

```
POST /Libreria/carrito/{id}/convertir-a-pedido/
```

**Proceso interno**:
1. Verifica que el carrito tenga productos
2. Verifica stock disponible para todos los productos
3. Crea un nuevo pedido con los mismos productos
4. Disminuye el stock de cada producto
5. Marca el carrito como inactivo
6. Calcula descuentos según reglas de negocio

**Respuesta**:
```json
{
  "mensaje": "Carrito convertido a pedido exitosamente.",
  "pedido_id": 1
}
```

## Endpoints de Detalles del Carrito

### Agregar Producto al Carrito
Agrega un producto al carrito activo del usuario.

```
POST /Libreria/detalle-carrito/
{
  "producto_id": 1,
  "cantidad": 2
}
```

**Proceso interno**:
1. Valida que la cantidad sea mayor que cero
2. Verifica que haya suficiente stock
3. Busca si el producto ya existe en el carrito:
   - Si existe: incrementa la cantidad (verificando stock)
   - Si no existe: crea un nuevo detalle
4. Calcula precio unitario y subtotal automáticamente

**Respuesta**:
```json
{
  "id": 1,
  "producto": {
    "id": 1,
    "nombre": "Cien años de soledad",
    "precio": "25.99",
    "stock": 10
  },
  "cantidad": 2,
  "precio_unitario": "25.99",
  "subtotal": "51.98"
}
```

### Listar Productos en el Carrito
Muestra todos los productos en el carrito activo.

```
GET /Libreria/detalle-carrito/
```

### Modificar Cantidad de un Producto
Actualiza la cantidad de un producto específico en el carrito.

```
PUT /Libreria/detalle-carrito/{id}/
{
  "producto_id": 1,
  "cantidad": 3
}
```

**Proceso interno**:
1. Valida que la cantidad sea mayor que cero
2. Verifica que haya suficiente stock
3. Actualiza la cantidad y recalcula el subtotal

### Eliminar Producto del Carrito
Elimina un producto específico del carrito.

```
DELETE /Libreria/detalle-carrito/{id}/
```

## Endpoints de Pedidos

### Crear Pedido Directamente
Crea un nuevo pedido sin usar el carrito (método alternativo).

```
POST /Libreria/pedidos/
{
  "usuario": 1,
  "detalles": [
    {
      "producto": 1,
      "cantidad": 2
    },
    {
      "producto": 3,
      "cantidad": 1
    }
  ]
}
```

**Proceso interno**:
1. Crea un nuevo pedido para el usuario
2. Para cada detalle:
   - Verifica stock disponible
   - Disminuye stock del producto
   - Calcula precio unitario y subtotal
3. Calcula el total y aplica descuentos automáticamente

### Listar Pedidos del Usuario
Muestra todos los pedidos del usuario autenticado.

```
GET /Libreria/pedidos/
```

### Ver Detalles de un Pedido
Muestra la información completa de un pedido específico.

```
GET /Libreria/pedidos/{id}/
```

### Calificar Pedido
Permite al usuario calificar un pedido existente.

```
POST /Libreria/pedidos/{id}/calificar/
{
  "calificacion": 5
}
```

**Validaciones**:
- La calificación debe estar entre 1 y 5
- Solo se puede calificar pedidos propios

**Respuesta**:
```json
{
  "detail": "Calificación actualizada con éxito."
}
```

### Calcular Total del Pedido
Recalcula el total del pedido aplicando descuentos (útil tras modificaciones).

```
POST /Libreria/pedidos/{id}/calcular-total/
```

**Respuesta**:
```json
{
  "total_actualizado": "135.75"
}
```

## Endpoints de Detalles de Pedidos

### Agregar Producto a un Pedido Existente
Agrega un nuevo producto a un pedido ya creado.

```
POST /Libreria/detalles/
{
  "pedido": 1,
  "producto": 2,
  "cantidad": 1
}
```

**Proceso interno**:
1. Verifica stock disponible
2. Disminuye stock del producto
3. Calcula precio unitario y subtotal
4. Recalcula el total del pedido incluyendo descuentos

### Listar Detalles de Pedidos
Muestra los detalles de todos los pedidos.

```
GET /Libreria/detalles/
```

### Modificar Detalle de Pedido
Actualiza la información de un detalle de pedido específico.

```
PUT /Libreria/detalles/{id}/
{
  "cantidad": 3
}
```

### Eliminar Detalle de Pedido
Elimina un producto específico de un pedido.

```
DELETE /Libreria/detalles/{id}/
```

## Flujo Completo de Compra

El flujo típico de una compra es el siguiente:

1. **Autenticación del usuario**:
   ```
   POST /Libreria/login/
   ```

2. **Obtención del carrito activo**:
   ```
   GET /Libreria/carrito/activo/
   ```

3. **Agregar productos al carrito** (repetir según necesidad):
   ```
   POST /Libreria/detalle-carrito/
   ```

4. **Revisar el carrito completo**:
   ```
   GET /Libreria/carrito/activo/
   ```

5. **Convertir el carrito a pedido**:
   ```
   POST /Libreria/carrito/{id}/convertir-a-pedido/
   ```

6. **Ver detalles del pedido creado**:
   ```
   GET /Libreria/pedidos/{id}/
   ```

7. **Calificar el pedido** (opcional, después de recibido):
   ```
   POST /Libreria/pedidos/{id}/calificar/
   ```

## Reglas de Negocio

### Gestión de Carritos
- Cada usuario tiene un solo carrito activo a la vez
- Al convertir un carrito a pedido, se marca como inactivo
- Los carritos inactivos se mantienen para análisis y recuperación

### Gestión de Stock
- Se verifica el stock al agregar productos al carrito
- Se verifica nuevamente al convertir carrito a pedido
- El stock se disminuye al crear un pedido o convertir un carrito

### Manejo de Duplicados
- Si un usuario agrega el mismo producto al carrito, se incrementa la cantidad
- Se verifica que el stock total sea suficiente para la cantidad acumulada

### Cálculo de Descuentos
Los descuentos se aplican automáticamente según el monto del pedido:
- Más de $600: 25% de descuento
- Más de $400: 15% de descuento
- Más de $200: 10% de descuento
- Menos de $200: Sin descuento

## Manejo de Errores

El sistema proporciona mensajes de error claros en los siguientes casos:

### Errores relacionados con el carrito:
- Intentar agregar cantidad negativa o cero
- Intentar agregar un producto sin stock suficiente
- Intentar convertir un carrito vacío a pedido

### Errores relacionados con pedidos:
- Intentar calificar con un valor fuera de rango (1-5)
- Intentar modificar un pedido con productos sin stock suficiente

### Errores de autenticación:
- Intentar acceder sin token de autenticación
- Intentar acceder a recursos de otro usuario

---

Para más información sobre la implementación técnica, consulte los archivos de código en:
- `pedidos/models.py`: Modelos de datos
- `pedidos/serializers.py`: Serialización y validación
- `pedidos/views.py`: Endpoints y lógica de negocio



pruebaaa commit
📅 **Fecha de última actualización**: [20/4/2025]

