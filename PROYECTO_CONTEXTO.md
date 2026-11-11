# 🛒 MercAPP IS2 — Documentación de Arquitectura por Capas y API REST

> **Asignatura:** Ingeniería de Software 2  
> **Proyecto:** MercAPP IS2 (Backend)  
> **Patrón Arquitectónico:** N-Capas (Layered Architecture) + API REST

---

## 1. 🏛️ Estructura del Backend por Capas

El backend se organiza en capas desacopladas con responsabilidades únicas:

```text
MercAPP_IS2_Backend/
│
├── controllers/          ──> Capa de Presentación / API REST
│   ├── __init__.py
│   ├── user_controller.py      # Endpoints HTTP /api/users
│   └── product_controller.py   # Endpoints HTTP /api/products y /api/categories
│
├── dtos/                 ──> Data Transfer Objects (Contratos de datos)
│   ├── __init__.py
│   ├── user_dto.py             # UserCreateDTO, UserUpdateDTO, UserResponseDTO
│   └── product_dto.py          # ProductCreateDTO, ProductUpdateDTO, ProductResponseDTO
│
├── services/             ──> Capa de Lógica de Negocio (Reglas de software)
│   ├── __init__.py
│   ├── user_service.py         # Validaciones, unicidad, hashing, autenticación
│   └── product_service.py      # Reglas de inventario, stock y catálogo
│
├── repositories/         ──> Capa de Acceso a Datos (Consultas a base de datos)
│   ├── __init__.py
│   ├── user_repository.py      # Operaciones CRUD sobre usuario
│   └── product_repository.py   # Operaciones CRUD sobre producto y categoría
│
├── models/               ──> Entidades de Base de Datos (SQLAlchemy)
│   ├── __init__.py
│   ├── database.py             # Instancia central compartida de SQLAlchemy
│   ├── user.py                 # Store, StoreSettings, User, Customer, AuditLog
│   └── product.py              # Category, Subcategory, Product
│
├── utilities/            ──> Módulos transversales
│   ├── __init__.py
│   ├── response_helper.py      # Formato estándar de respuestas JSON
│   └── security.py             # Cifrado de contraseñas
│
├── app.py                ──> Entrada de la aplicación y registro de Blueprints
└── requirements.txt      ──> Dependencias del backend
```

---

## 2. 🔄 Flujo de una Petición

```text
Cliente (Postman / Frontend)
           │
           │  Petición HTTP (GET, POST, PUT, DELETE) con Payload JSON
           ▼
[ CONTROLLER ]   Recibe HTTP, deserializa en DTO, llama al Service y devuelve JSON
           │
           │  DTO validado
           ▼
 [ SERVICE ]     Ejecuta lógica de negocio (validaciones, hashes, reglas)
           │
           │  Datos listos para persistir
           ▼
[ REPOSITORY ]  Ejecuta operaciones SQL con la base de datos (db.session)
           │
           ▼
 [ DATABASE ]   mercapp.db (SQLite)
```

---

## 3. 🌐 Endpoints REST Implementados

### Módulo de Usuarios (`/api/users`)
- `GET /api/users`: Lista todos los usuarios registrados (con passwords protegidos).
- `GET /api/users/<id>`: Obtiene el detalle de un usuario.
- `POST /api/users`: Crea un nuevo usuario validando campos y unicidad de email.
- `PUT /api/users/<id>`: Actualiza atributos de un usuario.
- `DELETE /api/users/<id>`: Elimina un usuario por ID.
- `POST /api/users/login`: Autentica credenciales y verifica estado activo.

### Módulo de Productos y Catálogo (`/api/products`, `/api/categories`)
- `GET /api/products`: Lista productos (soporta búsqueda con `?q=termino`).
- `GET /api/products/<id>`: Detalle de un producto por ID.
- `POST /api/products`: Crea un producto validando precio, categoría y código de barras.
- `PUT /api/products/<id>`: Actualiza información de stock, precio o datos del producto.
- `DELETE /api/products/<id>`: Desactiva un producto del catálogo (soft-delete).
- `GET /api/categories`: Lista las categorías del catálogo.
