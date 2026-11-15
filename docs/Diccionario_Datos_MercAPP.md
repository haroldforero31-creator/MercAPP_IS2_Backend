# Diccionario de Datos — MercAPP POS

**Sistema:** MercAPP · Punto de venta y gestión para minimercados  
**Alcance:** 28 tablas · 288 campos  
**Motores:** SQLite 3 (WAL) en local / MySQL 8.0+ (TiDB Cloud) en producción  
**ORM:** SQLAlchemy 2.0 (declarativo) · Flask-SQLAlchemy 3.1  
**Fecha de corte:** 14 de noviembre de 2026

> Documento generado desde los modelos SQLAlchemy (`models/*.py`) y verificado contra la base
> de datos real. Cada campo incluye tipo SQL, nulabilidad, clave, valor por defecto y descripción.

---

## 1. Resumen del modelo

| Métrica | Valor |
|---|---:|
| Tablas | 28 |
| Campos totales | 288 |
| Claves primarias | 28 (una por tabla) |
| Claves foráneas | 39 |
| Índices secundarios | 20 |
| Restricciones UNIQUE | 5 |
| Reglas ON DELETE / ON UPDATE | 0 |

### 1.1. Índice de tablas

| # | Módulo | Tabla física | Entidad | Campos | FK | Índices | Propósito |
|---:|---|---|---|---:|---:|---:|---|
| 1 | Núcleo del sistema y configuración | `tienda` | Store | 4 | 0 | 0 | Entidad raíz del modelo multi-tenant. Representa un negocio o supermercado registrado. |
| 2 | Núcleo del sistema y configuración | `configuracion_tienda` | StoreSettings | 30 | 1 | 0 | Parámetros operativos, fiscales DIAN, hardware (impresoras/básculas) y personalización visual. |
| 3 | Núcleo del sistema y configuración | `usuario` | User | 13 | 1 | 0 | Usuarios del sistema administrativo y operativo (Administrador y Cajero) con control de acceso y seguridad. |
| 4 | Núcleo del sistema y configuración | `cliente` | Customer | 7 | 0 | 0 | Clientes finales que compran en el Storefront Online (E-Commerce). |
| 5 | Núcleo del sistema y configuración | `app_license` | AppLicense | 3 | 0 | 0 | Control de vigencia y expiración de licencia del software para instalación local o comercial. |
| 6 | Catálogo de productos | `categoria` | Category | 8 | 1 | 1 | Categorías principales de productos en el catálogo comercial. |
| 7 | Catálogo de productos | `subcategoria` | Subcategory | 7 | 2 | 2 | Subcategorías para clasificación fina de productos. |
| 8 | Catálogo de productos | `producto` | Product | 16 | 3 | 5 | Catálogo maestro de artículos para venta por código de barras o balanza de peso. |
| 9 | Operación de caja y ventas | `sesion_caja` | CashSession | 12 | 2 | 2 | Turnos de caja. Control de apertura, base inicial, arqueo y cierre diario. |
| 10 | Operación de caja y ventas | `venta` | Sale | 17 | 4 | 7 | Cabecera de la transacción de venta registrada en POS o convertida desde pedido online. |
| 11 | Operación de caja y ventas | `detalle_venta` | SaleItem | 8 | 2 | 0 | Renglones o ítems incluidos en cada ticket de venta. |
| 12 | Crédito y cartera (fiados) | `cliente_credito` | CreditClient | 7 | 1 | 0 | Clientes de crédito local ("clientes de confianza" / libreta de fiado). |
| 13 | Crédito y cartera (fiados) | `venta_credito` | CreditSale | 7 | 2 | 0 | Obligación de deuda generada cuando una venta se factura a crédito ("fiado"). |
| 14 | Crédito y cartera (fiados) | `pago_credito` | CreditPayment | 6 | 1 | 0 | Abonos y cancelaciones realizados por un cliente a su cartera de crédito. |
| 15 | Portal de proveedores | `proveedor` | Supplier | 15 | 1 | 0 | Proveedores comerciales y distribuidores con acceso opcional al portal de proveedores. |
| 16 | Portal de proveedores | `orden_compra` | PurchaseOrder | 9 | 2 | 0 | Órdenes de abastecimiento emitidas por la tienda a un proveedor específico. |
| 17 | Portal de proveedores | `orden_compra_item` | PurchaseOrderItem | 8 | 2 | 0 | Artículos y cantidades solicitadas en una orden de compra. |
| 18 | Portal de proveedores | `factura_proveedor` | SupplierInvoice | 11 | 2 | 0 | Facturas comerciales por cobrar recibidas de los distribuidores mayoristas. |
| 19 | Portal de proveedores | `entrega_proveedor` | SupplierDelivery | 15 | 3 | 0 | Despachos físicos y pagos inmediatos en caja realizados a proveedores en tienda. |
| 20 | Portal de proveedores | `verificacion_email_proveedor` | SupplierEmailVerification | 11 | 0 | 0 | Validación por correo para autorregistro de proveedores mayoristas en el portal. |
| 21 | Tienda en línea (e-commerce) | `pedido` | Order | 16 | 4 | 2 | Pedidos en línea recibidos desde el catálogo virtual (storefront web). |
| 22 | Tienda en línea (e-commerce) | `detalle_pedido` | OrderItem | 8 | 2 | 0 | Productos y cantidades solicitadas en un pedido de la tienda virtual. |
| 23 | Tienda en línea (e-commerce) | `notificacion_pedido` | OrderNotification | 5 | 1 | 0 | Mensajes y actualizaciones enviadas al cliente sobre el estado de su pedido. |
| 24 | Seguridad, auditoría y correo | `auditoria` | AuditLog | 7 | 1 | 1 | Bitácora inmutable de seguridad. Registra cada acción crítica, login, anulación y modificación. |
| 25 | Seguridad, auditoría y correo | `cola_correos` | EmailQueue | 11 | 0 | 0 | Cola persistente para envíos asíncronos de correo con soporte de reintentos y tolerancia a fallos. |
| 26 | Seguridad, auditoría y correo | `verificacion_email` | EmailVerification | 10 | 0 | 0 | Códigos OTP de verificación para registro de nuevas tiendas y administradores. |
| 27 | Seguridad, auditoría y correo | `verificacion_email_cliente` | CustomerEmailVerification | 11 | 0 | 0 | Validación de correo electrónico para nuevos clientes del storefront online. |
| 28 | Seguridad, auditoría y correo | `recuperacion_contrasena` | PasswordReset | 6 | 1 | 0 | Tokens seguros con caducidad para el flujo de restablecimiento de contraseña olvidada. |

---

## 2. Diccionario por tabla

### Núcleo del sistema y configuración

#### 1. `tienda` — Store

**Propósito:** Entidad raíz del modelo multi-tenant. Representa un negocio o supermercado registrado.

**Clave primaria:** `id` · **Campos:** 4 · **Foráneas:** 0 · **Índices:** 0 · **Únicos:** 0

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador único de la tienda |
| 2 | `name` | VARCHAR(100) | NO | — | — | Nombre comercial de la tienda |
| 3 | `created_at` | DATETIME | SÍ | — | app: calculado | Fecha y hora de registro |
| 4 | `is_active` | BOOLEAN | SÍ | — | app: True | Estado operativo de la tienda |

---

#### 2. `configuracion_tienda` — StoreSettings

**Propósito:** Parámetros operativos, fiscales DIAN, hardware (impresoras/básculas) y personalización visual.

**Clave primaria:** `id` · **Campos:** 30 · **Foráneas:** 1 · **Índices:** 0 · **Únicos:** 0

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador único |
| 2 | `store_id` | INTEGER | NO | FK → tienda.id | — | Tienda asociada |
| 3 | `store_name` | VARCHAR(100) | SÍ | — | app: MercAPP | Nombre para tickets y reportes |
| 4 | `logo` | VARCHAR(200) | SÍ | — | app: logo.png | Ruta del logo institucional |
| 5 | `qr_transferencia` | VARCHAR(200) | SÍ | — | app:  | Ruta del código QR de pagos bancarios |
| 6 | `razon_social` | VARCHAR(200) | SÍ | — | app: MercAPP S.A.S | Razón social legal |
| 7 | `nit` | VARCHAR(20) | SÍ | — | app: 000.000.000-0 | NIT tributario |
| 8 | `rut` | VARCHAR(30) | SÍ | — | app:  | Número de RUT |
| 9 | `regimen_tributario` | VARCHAR(100) | SÍ | — | app: No responsable de IVA | Régimen tributario aplicable |
| 10 | `gran_contribuyente` | VARCHAR(100) | SÍ | — | app:  | Resolución DIAN gran contribuyente |
| 11 | `agente_retencion` | VARCHAR(100) | SÍ | — | app:  | Resolución agente retenedor |
| 12 | `direccion` | VARCHAR(200) | SÍ | — | app:  | Dirección física del establecimiento |
| 13 | `telefono` | VARCHAR(20) | SÍ | — | app:  | Teléfono de contacto comercial |
| 14 | `ciudad` | VARCHAR(100) | SÍ | — | app:  | Ciudad y departamento |
| 15 | `resolucion_dian` | VARCHAR(100) | SÍ | — | app:  | Número de resolución DIAN |
| 16 | `resolucion_fecha` | VARCHAR(50) | SÍ | — | app:  | Fecha de vigencia DIAN |
| 17 | `rango_desde` | VARCHAR(30) | SÍ | — | app: MRC-0001 | Prefijo y consecutivo inicial |
| 18 | `rango_hasta` | VARCHAR(30) | SÍ | — | app: MRC-9999 | Prefijo y consecutivo final |
| 19 | `mensaje_ticket` | VARCHAR(200) | SÍ | — | app: ¡Gracias por su compra! | Pie de página del ticket |
| 20 | `scale_mode` | VARCHAR(10) | SÍ | — | app: manual | Modo de pesaje: `manual` o `auto` |
| 21 | `printer_name` | VARCHAR(200) | SÍ | — | app:  | Nombre de la impresora térmica en Windows |
| 22 | `auto_print` | BOOLEAN | SÍ | — | app: True | Impresión automática al cobrar |
| 23 | `auto_drawer` | BOOLEAN | SÍ | — | app: True | Disparo automático del cajón de dinero |
| 24 | `theme_color_primary` | VARCHAR(20) | SÍ | — | app: default | Color primario de interfaz |
| 25 | `theme_color_accent` | VARCHAR(20) | SÍ | — | app: default | Color de acento |
| 26 | `theme_color_background` | VARCHAR(20) | SÍ | — | app: default | Fondo general |
| 27 | `theme_font_family` | VARCHAR(50) | SÍ | — | app: default | Tipografía de UI |
| 28 | `theme_font_size` | VARCHAR(15) | SÍ | — | app: default | Escala de fuente |
| 29 | `theme_btn_clear_color` | VARCHAR(20) | SÍ | — | app: default | Estilo botón limpiar |
| 30 | `theme_btn_charge_color` | VARCHAR(20) | SÍ | — | app: default | Estilo botón cobrar |

**Restricciones y accesos:**

- FK `store_id` → `tienda.id`

---

#### 3. `usuario` — User

**Propósito:** Usuarios del sistema administrativo y operativo (Administrador y Cajero) con control de acceso y seguridad.

**Clave primaria:** `id` · **Campos:** 13 · **Foráneas:** 1 · **Índices:** 0 · **Únicos:** 1

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador único |
| 2 | `store_id` | INTEGER | NO | FK → tienda.id | — | Tienda a la que pertenece |
| 3 | `name` | VARCHAR(100) | NO | — | — | Nombre y apellidos completos |
| 4 | `username` | VARCHAR(50) | SÍ | — | — | Alias o usuario corto opcional |
| 5 | `email` | VARCHAR(120) | NO | UQ | — | Correo para inicio de sesión |
| 6 | `password_hash` | VARCHAR(255) | NO | — | — | Hash scrypt/PBKDF2 de la clave |
| 7 | `is_admin` | BOOLEAN | SÍ | — | app: True | Rol: Administrador (`True`) o Cajero (`False`) |
| 8 | `is_active_cashier` | BOOLEAN | SÍ | — | app: True | Permiso operativo para abrir caja |
| 9 | `status` | VARCHAR(20) | SÍ | — | app: ACTIVO | Estado: `ACTIVO` o `BLOQUEADO` |
| 10 | `failed_attempts` | INTEGER | SÍ | — | app: 0 | Contador de intentos fallidos consecutivos |
| 11 | `locked_until` | DATETIME | SÍ | — | — | Timestamp hasta el cual la cuenta está suspendida (15 min) |
| 12 | `last_login` | DATETIME | SÍ | — | — | Última fecha y hora de sesión exitosa |
| 13 | `created_at` | DATETIME | SÍ | — | app: calculado | Fecha de registro |

**Restricciones y accesos:**

- FK `store_id` → `tienda.id`
- UNIQUE (`email`)

---

#### 4. `cliente` — Customer

**Propósito:** Clientes finales que compran en el Storefront Online (E-Commerce).

**Clave primaria:** `id` · **Campos:** 7 · **Foráneas:** 0 · **Índices:** 0 · **Únicos:** 1

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador único |
| 2 | `name` | VARCHAR(100) | SÍ | — | — | Nombre completo del comprador |
| 3 | `email` | VARCHAR(100) | SÍ | UQ | — | Correo para login en tienda web |
| 4 | `phone` | VARCHAR(20) | SÍ | — | — | Teléfono móvil para avisos |
| 5 | `address` | VARCHAR(200) | SÍ | — | — | Dirección predeterminada de entrega |
| 6 | `password_hash` | VARCHAR(255) | SÍ | — | — | Hash de la contraseña del cliente |
| 7 | `created_at` | DATETIME | SÍ | — | app: calculado | Fecha de registro en el storefront |

**Restricciones y accesos:**

- UNIQUE (`email`)

---

#### 5. `app_license` — AppLicense

**Propósito:** Control de vigencia y expiración de licencia del software para instalación local o comercial.

**Clave primaria:** `id` · **Campos:** 3 · **Foráneas:** 0 · **Índices:** 0 · **Únicos:** 0

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador único |
| 2 | `expiration_date` | DATETIME | NO | — | — | Fecha y hora en que expira la licencia comercial |
| 3 | `last_time_checked` | DATETIME | SÍ | — | — | Timestamp del último chequeo contra reloj seguro |

---

### Catálogo de productos

#### 6. `categoria` — Category

**Propósito:** Categorías principales de productos en el catálogo comercial.

**Clave primaria:** `id` · **Campos:** 8 · **Foráneas:** 1 · **Índices:** 1 · **Únicos:** 0

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador único |
| 2 | `store_id` | INTEGER | NO | FK → tienda.id · IX | — | Tienda propietaria |
| 3 | `name` | VARCHAR(50) | NO | — | — | Nombre de la categoría (ej. Lácteos) |
| 4 | `slug` | VARCHAR(50) | NO | — | — | Slug amigable para URLs |
| 5 | `image` | VARCHAR(200) | SÍ | — | app: default_category.png | Icono o imagen ilustrativa |
| 6 | `description` | VARCHAR(200) | SÍ | — | — | Descripción comercial |
| 7 | `display_order` | INTEGER | SÍ | — | app: 0 | Orden de aparición en botones POS |
| 8 | `visible_in_pos` | BOOLEAN | SÍ | — | app: True | Si es visible en la cuadrícula de ventas |

**Restricciones y accesos:**

- FK `store_id` → `tienda.id`
- INDEX `ix_categoria_store_id` (`store_id`)

---

#### 7. `subcategoria` — Subcategory

**Propósito:** Subcategorías para clasificación fina de productos.

**Clave primaria:** `id` · **Campos:** 7 · **Foráneas:** 2 · **Índices:** 2 · **Únicos:** 0

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador único |
| 2 | `store_id` | INTEGER | NO | FK → tienda.id · IX | — | Tienda propietaria |
| 3 | `name` | VARCHAR(50) | NO | — | — | Nombre de la subcategoría |
| 4 | `slug` | VARCHAR(50) | NO | — | — | Slug identificador |
| 5 | `category_id` | INTEGER | NO | FK → categoria.id · IX | — | Categoría padre |
| 6 | `image` | VARCHAR(200) | SÍ | — | app: default_subcategory.png | Imagen opcional |
| 7 | `display_order` | INTEGER | SÍ | — | app: 0 | Posición en menú |

**Restricciones y accesos:**

- FK `store_id` → `tienda.id`
- FK `category_id` → `categoria.id`
- INDEX `ix_subcategoria_category_id` (`category_id`)
- INDEX `ix_subcategoria_store_id` (`store_id`)

---

#### 8. `producto` — Product

**Propósito:** Catálogo maestro de artículos para venta por código de barras o balanza de peso.

**Clave primaria:** `id` · **Campos:** 16 · **Foráneas:** 3 · **Índices:** 5 · **Únicos:** 0

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador único |
| 2 | `store_id` | INTEGER | NO | FK → tienda.id · IX | — | Tienda propietaria |
| 3 | `name` | VARCHAR(150) | NO | — | — | Nombre y presentación del producto |
| 4 | `barcode` | VARCHAR(60) | SÍ | IX | — | Código de barras EAN-13 o manual |
| 5 | `price` | INTEGER | NO | — | — | Precio de venta en pesos colombianos (COP) |
| 6 | `category_id` | INTEGER | NO | FK → categoria.id · IX | — | Categoría asociada |
| 7 | `subcategory_id` | INTEGER | SÍ | FK → subcategoria.id | — | Subcategoría opcional |
| 8 | `image` | VARCHAR(200) | SÍ | — | app: default_product.png | Imagen del producto |
| 9 | `has_barcode` | BOOLEAN | SÍ | — | app: False | Si utiliza lector o búsqueda rápida |
| 10 | `stock` | INTEGER | SÍ | — | — | Cantidad de unidades o gramos disponibles |
| 11 | `sell_by_weight` | BOOLEAN | SÍ | — | app: False | Flag para productos pesables en balanza |
| 12 | `weight_unit` | VARCHAR(5) | SÍ | — | app: kg | Unidad de peso (`kg`, `g`, `lb`) |
| 13 | `plu_code` | VARCHAR(60) | SÍ | — | — | Código PLU de balanza para frutas/verduras |
| 14 | `sale_count` | INTEGER | SÍ | — | app: 0 | Métricas de ventas acumuladas |
| 15 | `is_active` | BOOLEAN | SÍ | — | app: True | Estado activo/desactivado |
| 16 | `created_at` | DATETIME | SÍ | — | app: calculado | Fecha de alta en inventario |

**Restricciones y accesos:**

- FK `store_id` → `tienda.id`
- FK `category_id` → `categoria.id`
- FK `subcategory_id` → `subcategoria.id`
- INDEX `idx_producto_store_barcode` (`store_id`, `barcode`)
- INDEX `idx_producto_store_id` (`store_id`)
- INDEX `ix_producto_barcode` (`barcode`)
- INDEX `ix_producto_category_id` (`category_id`)
- INDEX `ix_producto_store_id` (`store_id`)

---

### Operación de caja y ventas

#### 9. `sesion_caja` — CashSession

**Propósito:** Turnos de caja. Control de apertura, base inicial, arqueo y cierre diario.

**Clave primaria:** `id` · **Campos:** 12 · **Foráneas:** 2 · **Índices:** 2 · **Únicos:** 0

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador de la sesión de caja |
| 2 | `store_id` | INTEGER | NO | FK → tienda.id · IX | — | Tienda |
| 3 | `user_id` | INTEGER | NO | FK → usuario.id | — | Cajero responsable del turno |
| 4 | `opened_at` | DATETIME | SÍ | — | app: calculado | Fecha y hora de apertura |
| 5 | `closed_at` | DATETIME | SÍ | — | — | Fecha y hora de cierre del turno |
| 6 | `base_amount` | INTEGER | NO | — | app: 0 | Dinero base en caja al iniciar |
| 7 | `cash_sales` | INTEGER | SÍ | — | app: 0 | Total ventas en efectivo |
| 8 | `card_sales` | INTEGER | SÍ | — | app: 0 | Total ventas con tarjeta |
| 9 | `transfer_sales` | INTEGER | SÍ | — | app: 0 | Total ventas transferencia (Nequi/Daviplata) |
| 10 | `expected_cash` | INTEGER | SÍ | — | app: 0 | Efectivo teórico esperado (base + ventas - pagos) |
| 11 | `actual_cash` | INTEGER | SÍ | — | — | Efectivo real contado en el arqueo físico |
| 12 | `status` | VARCHAR(20) | SÍ | — | app: abierta | Estado: `abierta` o `cerrada` |

**Restricciones y accesos:**

- FK `store_id` → `tienda.id`
- FK `user_id` → `usuario.id`
- INDEX `idx_sesion_caja_store_status` (`store_id`, `status`)
- INDEX `ix_sesion_caja_store_id` (`store_id`)

---

#### 10. `venta` — Sale

**Propósito:** Cabecera de la transacción de venta registrada en POS o convertida desde pedido online.

**Clave primaria:** `id` · **Campos:** 17 · **Foráneas:** 4 · **Índices:** 7 · **Únicos:** 0

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador de la venta |
| 2 | `store_id` | INTEGER | NO | FK → tienda.id · IX | — | Tienda |
| 3 | `cash_session_id` | INTEGER | SÍ | FK → sesion_caja.id · IX | — | Turno de caja en que ocurrió |
| 4 | `credit_client_id` | INTEGER | SÍ | FK → cliente_credito.id | — | Cliente de crédito si aplica ("fiado") |
| 5 | `receipt_number` | VARCHAR(30) | NO | UQ · IX | — | Número de consecutivo de ticket (ej. MRC-0042) |
| 6 | `user_id` | INTEGER | NO | FK → usuario.id | — | Cajero que ejecutó el cobro |
| 7 | `sale_date` | DATETIME | SÍ | IX | app: calculado | Fecha y hora exacta de la compra |
| 8 | `subtotal` | INTEGER | NO | — | — | Subtotal antes de impuestos/ajustes |
| 9 | `total` | INTEGER | NO | — | — | Valor total pagado |
| 10 | `payment_method` | VARCHAR(20) | NO | — | — | Medio: `efectivo`, `tarjeta`, `transferencia`, `credito`, `mixto` |
| 11 | `amount_received` | INTEGER | SÍ | — | app: 0 | Dinero entregado por el cliente |
| 12 | `change_given` | INTEGER | SÍ | — | app: 0 | Cambio o devuelta entregada |
| 13 | `payment_ref` | VARCHAR(100) | SÍ | — | — | Referencia de transacción bancaria |
| 14 | `amount_cash` | INTEGER | SÍ | — | app: 0 | Porción en efectivo (pago mixto) |
| 15 | `amount_card` | INTEGER | SÍ | — | app: 0 | Porción en tarjeta (pago mixto) |
| 16 | `amount_transfer` | INTEGER | SÍ | — | app: 0 | Porción por transferencia (pago mixto) |
| 17 | `status` | VARCHAR(20) | SÍ | — | app: completada | Estado: `completada` o `anulada` |

**Restricciones y accesos:**

- FK `store_id` → `tienda.id`
- FK `cash_session_id` → `sesion_caja.id`
- FK `credit_client_id` → `cliente_credito.id`
- FK `user_id` → `usuario.id`
- INDEX `idx_venta_session` (`cash_session_id`)
- INDEX `idx_venta_store_date` (`store_id`, `sale_date`)
- INDEX `idx_venta_store_id` (`store_id`)
- INDEX `ix_venta_cash_session_id` (`cash_session_id`)
- UNIQUE INDEX `ix_venta_receipt_number` (`receipt_number`)
- INDEX `ix_venta_sale_date` (`sale_date`)
- INDEX `ix_venta_store_id` (`store_id`)

---

#### 11. `detalle_venta` — SaleItem

**Propósito:** Renglones o ítems incluidos en cada ticket de venta.

**Clave primaria:** `id` · **Campos:** 8 · **Foráneas:** 2 · **Índices:** 0 · **Únicos:** 0

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador del renglón |
| 2 | `sale_id` | INTEGER | NO | FK → venta.id | — | Venta asociada |
| 3 | `product_id` | INTEGER | NO | FK → producto.id | — | Producto vendido |
| 4 | `quantity` | INTEGER | NO | — | — | Unidades vendidas (o 1 si es por peso) |
| 5 | `unit_price` | INTEGER | NO | — | — | Precio unitario al momento de venta |
| 6 | `subtotal` | INTEGER | NO | — | — | Total del ítem (`quantity` × `unit_price`) |
| 7 | `weight_grams` | INTEGER | SÍ | — | — | Gramos exactos en caso de producto de báscula |
| 8 | `weight_unit` | VARCHAR(5) | SÍ | — | — | Unidad de medida (`kg`, `g`, `lb`) |

**Restricciones y accesos:**

- FK `sale_id` → `venta.id`
- FK `product_id` → `producto.id`

---

### Crédito y cartera (fiados)

#### 12. `cliente_credito` — CreditClient

**Propósito:** Clientes de crédito local ("clientes de confianza" / libreta de fiado).

**Clave primaria:** `id` · **Campos:** 7 · **Foráneas:** 1 · **Índices:** 0 · **Únicos:** 0

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador único |
| 2 | `store_id` | INTEGER | NO | FK → tienda.id | — | Tienda |
| 3 | `name` | VARCHAR(100) | NO | — | — | Nombre completo del cliente de crédito |
| 4 | `phone` | VARCHAR(20) | SÍ | — | — | Teléfono para cobranza y WhatsApp |
| 5 | `email` | VARCHAR(120) | SÍ | — | — | Correo de contacto |
| 6 | `is_active` | BOOLEAN | SÍ | — | app: True | Estado activo para otorgar nuevo crédito |
| 7 | `created_at` | DATETIME | SÍ | — | app: calculado | Fecha de registro |

**Restricciones y accesos:**

- FK `store_id` → `tienda.id`

---

#### 13. `venta_credito` — CreditSale

**Propósito:** Obligación de deuda generada cuando una venta se factura a crédito ("fiado").

**Clave primaria:** `id` · **Campos:** 7 · **Foráneas:** 2 · **Índices:** 0 · **Únicos:** 0

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador único del crédito |
| 2 | `client_id` | INTEGER | NO | FK → cliente_credito.id | — | Cliente deudor |
| 3 | `sale_id` | INTEGER | NO | FK → venta.id | — | Venta de origen |
| 4 | `amount` | INTEGER | NO | — | — | Monto total adeudado inicialmente |
| 5 | `balance` | INTEGER | NO | — | — | Saldo pendiente por pagar |
| 6 | `status` | VARCHAR(20) | SÍ | — | app: pendiente | Estado: `pendiente`, `parcial`, `pagada` |
| 7 | `created_at` | DATETIME | SÍ | — | app: calculado | Fecha de concesión del crédito |

**Restricciones y accesos:**

- FK `client_id` → `cliente_credito.id`
- FK `sale_id` → `venta.id`

---

#### 14. `pago_credito` — CreditPayment

**Propósito:** Abonos y cancelaciones realizados por un cliente a su cartera de crédito.

**Clave primaria:** `id` · **Campos:** 6 · **Foráneas:** 1 · **Índices:** 0 · **Únicos:** 0

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador del abono |
| 2 | `client_id` | INTEGER | NO | FK → cliente_credito.id | — | Cliente que abona |
| 3 | `amount` | INTEGER | NO | — | — | Valor del abono en COP |
| 4 | `payment_method` | VARCHAR(20) | SÍ | — | app: efectivo | Medio: `efectivo`, `transferencia`, `tarjeta` |
| 5 | `payment_date` | DATETIME | SÍ | — | app: calculado | Fecha y hora del abono |
| 6 | `notes` | VARCHAR(200) | SÍ | — | — | Observaciones o recibo físico |

**Restricciones y accesos:**

- FK `client_id` → `cliente_credito.id`

---

### Portal de proveedores

#### 15. `proveedor` — Supplier

**Propósito:** Proveedores comerciales y distribuidores con acceso opcional al portal de proveedores.

**Clave primaria:** `id` · **Campos:** 15 · **Foráneas:** 1 · **Índices:** 0 · **Únicos:** 1

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador único |
| 2 | `store_id` | INTEGER | SÍ | FK → tienda.id | — | Tienda asociada |
| 3 | `company_name` | VARCHAR(150) | NO | — | — | Razón social de la empresa proveedora |
| 4 | `contact_name` | VARCHAR(100) | SÍ | — | — | Nombre del asesor comercial o despachador |
| 5 | `nit` | VARCHAR(30) | SÍ | — | — | NIT o cédula jurídica |
| 6 | `email` | VARCHAR(120) | NO | UQ | — | Correo para login en portal y facturación |
| 7 | `phone` | VARCHAR(30) | SÍ | — | — | Teléfono o celular de contacto |
| 8 | `address` | VARCHAR(200) | SÍ | — | — | Dirección del centro de distribución |
| 9 | `category_type` | VARCHAR(100) | SÍ | — | app: General | Rubro (Bebidas, Cárnicos, Abarrotes, etc.) |
| 10 | `payment_terms_days` | INTEGER | SÍ | — | app: 30 | Días de plazo de pago acordados |
| 11 | `credit_limit` | INTEGER | SÍ | — | app: 10000000 | Límite de cupo de crédito otorgado al negocio |
| 12 | `total_debt` | INTEGER | SÍ | — | app: 0 | Saldo adeudado acumulado al proveedor |
| 13 | `password_hash` | VARCHAR(255) | SÍ | — | — | Clave encriptada para login de proveedor |
| 14 | `status` | VARCHAR(20) | SÍ | — | app: ACTIVO | Estado: `ACTIVO` o `SUSPENDIDO` |
| 15 | `created_at` | DATETIME | SÍ | — | app: calculado | Fecha de alta |

**Restricciones y accesos:**

- FK `store_id` → `tienda.id`
- UNIQUE (`email`)

---

#### 16. `orden_compra` — PurchaseOrder

**Propósito:** Órdenes de abastecimiento emitidas por la tienda a un proveedor específico.

**Clave primaria:** `id` · **Campos:** 9 · **Foráneas:** 2 · **Índices:** 0 · **Únicos:** 1

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador único de orden |
| 2 | `store_id` | INTEGER | NO | FK → tienda.id | — | Tienda emisora |
| 3 | `supplier_id` | INTEGER | NO | FK → proveedor.id | — | Proveedor destinatario |
| 4 | `order_number` | VARCHAR(50) | NO | UQ | — | Consecutivo de orden (ej. OC-2026-001) |
| 5 | `status` | VARCHAR(30) | SÍ | — | app: PENDIENTE | Estado: `PENDIENTE`, `APROBADA`, `RECIBIDA`, `CANCELADA` |
| 6 | `total_estimated` | INTEGER | SÍ | — | app: 0 | Costo estimado total de la compra |
| 7 | `notes` | TEXT | SÍ | — | — | Instrucciones especiales de despacho |
| 8 | `expected_delivery` | DATETIME | SÍ | — | — | Fecha programada de arribo |
| 9 | `created_at` | DATETIME | SÍ | — | app: calculado | Fecha de expedición |

**Restricciones y accesos:**

- FK `store_id` → `tienda.id`
- FK `supplier_id` → `proveedor.id`
- UNIQUE (`order_number`)

---

#### 17. `orden_compra_item` — PurchaseOrderItem

**Propósito:** Artículos y cantidades solicitadas en una orden de compra.

**Clave primaria:** `id` · **Campos:** 8 · **Foráneas:** 2 · **Índices:** 0 · **Únicos:** 0

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador del ítem |
| 2 | `order_id` | INTEGER | NO | FK → orden_compra.id | — | Orden de compra asociada |
| 3 | `product_id` | INTEGER | SÍ | FK → producto.id | — | Producto del catálogo si existe |
| 4 | `product_name` | VARCHAR(150) | NO | — | — | Nombre del producto |
| 5 | `quantity_ordered` | INTEGER | NO | — | app: 1 | Cantidad pedida |
| 6 | `quantity_received` | INTEGER | SÍ | — | app: 0 | Cantidad físicamente recibida en almacén |
| 7 | `unit_cost` | INTEGER | SÍ | — | app: 0 | Costo unitario acordado |
| 8 | `subtotal` | INTEGER | SÍ | — | app: 0 | Total renglón (`quantity_ordered` × `unit_cost`) |

**Restricciones y accesos:**

- FK `order_id` → `orden_compra.id`
- FK `product_id` → `producto.id`

---

#### 18. `factura_proveedor` — SupplierInvoice

**Propósito:** Facturas comerciales por cobrar recibidas de los distribuidores mayoristas.

**Clave primaria:** `id` · **Campos:** 11 · **Foráneas:** 2 · **Índices:** 0 · **Únicos:** 0

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador único |
| 2 | `store_id` | INTEGER | NO | FK → tienda.id | — | Tienda deudora |
| 3 | `supplier_id` | INTEGER | NO | FK → proveedor.id | — | Proveedor emisor |
| 4 | `invoice_number` | VARCHAR(50) | NO | — | — | Número de factura del proveedor |
| 5 | `issue_date` | DATETIME | SÍ | — | app: calculado | Fecha de expedición |
| 6 | `due_date` | DATETIME | NO | — | — | Fecha límite de pago de la factura |
| 7 | `total_amount` | INTEGER | NO | — | — | Monto total a pagar |
| 8 | `paid_amount` | INTEGER | SÍ | — | app: 0 | Monto abonado o cancelado |
| 9 | `status` | VARCHAR(30) | SÍ | — | app: PENDIENTE | Estado: `PENDIENTE`, `PAGADA_PARCIAL`, `PAGADA` |
| 10 | `notes` | TEXT | SÍ | — | — | Notas adicionales de pago |
| 11 | `created_at` | DATETIME | SÍ | — | app: calculado | Fecha de registro en el sistema |

**Restricciones y accesos:**

- FK `store_id` → `tienda.id`
- FK `supplier_id` → `proveedor.id`

---

#### 19. `entrega_proveedor` — SupplierDelivery

**Propósito:** Despachos físicos y pagos inmediatos en caja realizados a proveedores en tienda.

**Clave primaria:** `id` · **Campos:** 15 · **Foráneas:** 3 · **Índices:** 0 · **Únicos:** 0

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador de la entrega |
| 2 | `supplier_id` | INTEGER | NO | FK → proveedor.id | — | Proveedor que entrega mercancía |
| 3 | `store_id` | INTEGER | NO | FK → tienda.id | — | Tienda |
| 4 | `cash_session_id` | INTEGER | SÍ | FK → sesion_caja.id | — | Turno de caja si se pagó con dinero de caja |
| 5 | `order_number` | VARCHAR(60) | NO | — | — | Consecutivo o remisión |
| 6 | `delivery_date` | DATETIME | SÍ | — | app: calculado | Fecha y hora de recepción |
| 7 | `total_amount` | INTEGER | NO | — | — | Valor cancelado en la entrega |
| 8 | `payment_method` | VARCHAR(30) | SÍ | — | app: efectivo_caja | Medio de desembolso |
| 9 | `amount_cash` | INTEGER | SÍ | — | app: 0 | Valor pagado en efectivo |
| 10 | `amount_transfer` | INTEGER | SÍ | — | app: 0 | Valor pagado por transferencia |
| 11 | `notes` | TEXT | SÍ | — | — | Observaciones del cajero/almacenista |
| 12 | `invoice_photo` | VARCHAR(255) | SÍ | — | — | Foto comprobante de la remisión física |
| 13 | `is_confirmed` | BOOLEAN | SÍ | — | app: True | Confirmación de recibido |
| 14 | `confirmed_at` | DATETIME | SÍ | — | app: calculado | Timestamp de confirmación |
| 15 | `created_at` | DATETIME | SÍ | — | app: calculado | Registro de entrega |

**Restricciones y accesos:**

- FK `supplier_id` → `proveedor.id`
- FK `store_id` → `tienda.id`
- FK `cash_session_id` → `sesion_caja.id`

---

#### 20. `verificacion_email_proveedor` — SupplierEmailVerification

**Propósito:** Validación por correo para autorregistro de proveedores mayoristas en el portal.

**Clave primaria:** `id` · **Campos:** 11 · **Foráneas:** 0 · **Índices:** 0 · **Únicos:** 0

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador único |
| 2 | `company_name` | VARCHAR(150) | NO | — | — | Empresa proveedora |
| 3 | `contact_name` | VARCHAR(100) | NO | — | — | Asesor comercial |
| 4 | `email` | VARCHAR(120) | NO | — | — | Correo corporativo |
| 5 | `phone` | VARCHAR(30) | NO | — | — | Teléfono |
| 6 | `password_hash` | VARCHAR(256) | NO | — | — | Clave segura |
| 7 | `code` | VARCHAR(10) | NO | — | — | Código OTP |
| 8 | `verified` | BOOLEAN | SÍ | — | app: False | Estado de verificación |
| 9 | `attempts` | INTEGER | SÍ | — | app: 0 | Intentos |
| 10 | `expires_at` | DATETIME | NO | — | — | Expiración |
| 11 | `created_at` | DATETIME | SÍ | — | app: calculado | Registro de emisión |

---

### Tienda en línea (e-commerce)

#### 21. `pedido` — Order

**Propósito:** Pedidos en línea recibidos desde el catálogo virtual (storefront web).

**Clave primaria:** `id` · **Campos:** 16 · **Foráneas:** 4 · **Índices:** 2 · **Únicos:** 0

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador del pedido |
| 2 | `store_id` | INTEGER | NO | FK → tienda.id · IX | — | Tienda que recibe el pedido |
| 3 | `customer_id` | INTEGER | SÍ | FK → cliente.id | — | Cliente registrado si aplica |
| 4 | `user_id` | INTEGER | SÍ | FK → usuario.id | — | Empleado que despachó el pedido |
| 5 | `sale_id` | INTEGER | SÍ | FK → venta.id | — | Venta generada cuando el pedido se factura en POS |
| 6 | `customer_name` | VARCHAR(100) | NO | — | — | Nombre de quien recibe |
| 7 | `customer_phone` | VARCHAR(20) | NO | — | — | Teléfono celular |
| 8 | `customer_address` | VARCHAR(200) | SÍ | — | — | Dirección de entrega a domicilio |
| 9 | `order_type` | VARCHAR(20) | SÍ | — | app: domicilio | Modalidad: `domicilio` o `recoger_tienda` |
| 10 | `payment_method` | VARCHAR(20) | SÍ | — | app: efectivo | Pago previsto (`efectivo`, `transferencia`, `tarjeta`) |
| 11 | `delivery_cost` | INTEGER | SÍ | — | app: 0 | Costo de envío a domicilio |
| 12 | `subtotal` | INTEGER | NO | — | app: 0 | Valor de los productos |
| 13 | `total` | INTEGER | NO | — | app: 0 | Total a cobrar (`subtotal` + `delivery_cost`) |
| 14 | `status` | VARCHAR(20) | SÍ | — | app: pendiente | Estado: `pendiente`, `en_preparacion`, `en_camino`, `entregado`, `cancelado` |
| 15 | `notes` | TEXT | SÍ | — | — | Observaciones del cliente |
| 16 | `created_at` | DATETIME | SÍ | — | app: calculado | Fecha y hora en que se envió el pedido |

**Restricciones y accesos:**

- FK `store_id` → `tienda.id`
- FK `customer_id` → `cliente.id`
- FK `user_id` → `usuario.id`
- FK `sale_id` → `venta.id`
- INDEX `idx_pedido_store_status` (`store_id`, `status`)
- INDEX `ix_pedido_store_id` (`store_id`)

---

#### 22. `detalle_pedido` — OrderItem

**Propósito:** Productos y cantidades solicitadas en un pedido de la tienda virtual.

**Clave primaria:** `id` · **Campos:** 8 · **Foráneas:** 2 · **Índices:** 0 · **Únicos:** 0

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador del ítem de pedido |
| 2 | `order_id` | INTEGER | NO | FK → pedido.id | — | Pedido asociado |
| 3 | `product_id` | INTEGER | NO | FK → producto.id | — | Producto ordenado |
| 4 | `quantity` | FLOAT | NO | — | — | Cantidad de unidades o peso |
| 5 | `unit_price` | INTEGER | NO | — | — | Precio pactado al enviar el pedido |
| 6 | `subtotal` | INTEGER | NO | — | — | Monto (`quantity` × `unit_price`) |
| 7 | `weight_grams` | INTEGER | SÍ | — | — | Gramos calculados si es por peso |
| 8 | `weight_unit` | VARCHAR(5) | SÍ | — | — | Unidad de medida (`kg`, `g`, `lb`) |

**Restricciones y accesos:**

- FK `order_id` → `pedido.id`
- FK `product_id` → `producto.id`

---

#### 23. `notificacion_pedido` — OrderNotification

**Propósito:** Mensajes y actualizaciones enviadas al cliente sobre el estado de su pedido.

**Clave primaria:** `id` · **Campos:** 5 · **Foráneas:** 1 · **Índices:** 0 · **Únicos:** 0

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador de la notificación |
| 2 | `order_id` | INTEGER | NO | FK → pedido.id | — | Pedido relacionado |
| 3 | `message` | TEXT | NO | — | — | Contenido del mensaje |
| 4 | `is_read` | BOOLEAN | NO | — | app: False | Si el cliente ya visualizó el aviso |
| 5 | `created_at` | DATETIME | SÍ | — | app: calculado | Timestamp de expedición |

**Restricciones y accesos:**

- FK `order_id` → `pedido.id`

---

### Seguridad, auditoría y correo

#### 24. `auditoria` — AuditLog

**Propósito:** Bitácora inmutable de seguridad. Registra cada acción crítica, login, anulación y modificación.

**Clave primaria:** `id` · **Campos:** 7 · **Foráneas:** 1 · **Índices:** 1 · **Únicos:** 0

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador del evento de auditoría |
| 2 | `user_id` | INTEGER | SÍ | FK → usuario.id | — | Usuario responsable (o null si anónimo) |
| 3 | `action` | VARCHAR(50) | NO | — | — | Operación: `LOGIN`, `LOGOUT`, `VENTA`, `ANULACION`, `CREACION_PRODUCTO`, etc. |
| 4 | `description` | TEXT | NO | — | — | Resumen detallado del suceso con IDs |
| 5 | `ip_address` | VARCHAR(45) | SÍ | — | app: 127.0.0.1 | Dirección IP cliente (soporta IPv4 e IPv6) |
| 6 | `severity` | VARCHAR(20) | SÍ | — | app: INFO | Nivel: `INFO`, `WARNING`, `CRITICAL` |
| 7 | `created_at` | DATETIME | SÍ | — | app: calculado | Marca temporal inmutable |

**Restricciones y accesos:**

- FK `user_id` → `usuario.id`
- INDEX `idx_auditoria_created` (`created_at`)

---

#### 25. `cola_correos` — EmailQueue

**Propósito:** Cola persistente para envíos asíncronos de correo con soporte de reintentos y tolerancia a fallos.

**Clave primaria:** `id` · **Campos:** 11 · **Foráneas:** 0 · **Índices:** 0 · **Únicos:** 0

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador del mensaje en cola |
| 2 | `store_id` | INTEGER | SÍ | — | — | Tienda originaria |
| 3 | `recipient` | VARCHAR(150) | NO | — | — | Buzón destino del correo |
| 4 | `subject` | VARCHAR(200) | NO | — | — | Asunto del mensaje |
| 5 | `html_body` | TEXT | NO | — | — | Cuerpo HTML con estilos inline y logo |
| 6 | `email_type` | VARCHAR(50) | SÍ | — | app: cierre_caja | Tipo: `cierre_caja`, `verificacion`, `recuperacion`, `orden_compra` |
| 7 | `status` | VARCHAR(20) | SÍ | — | app: pending | Estado: `pending`, `sent`, `failed` |
| 8 | `attempts` | INTEGER | SÍ | — | app: 0 | Contador de reintentos ejecutados |
| 9 | `last_error` | TEXT | SÍ | — | — | Traza de error SMTP si falló |
| 10 | `created_at` | DATETIME | SÍ | — | app: calculado | Fecha de encolamiento |
| 11 | `sent_at` | DATETIME | SÍ | — | — | Timestamp de confirmación de despacho |

---

#### 26. `verificacion_email` — EmailVerification

**Propósito:** Códigos OTP de verificación para registro de nuevas tiendas y administradores.

**Clave primaria:** `id` · **Campos:** 10 · **Foráneas:** 0 · **Índices:** 0 · **Únicos:** 0

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador único |
| 2 | `email` | VARCHAR(120) | NO | — | — | Correo a verificar |
| 3 | `code` | VARCHAR(10) | NO | — | — | Token OTP numérico |
| 4 | `store_name` | VARCHAR(100) | NO | — | — | Nombre de la tienda a dar de alta |
| 5 | `user_name` | VARCHAR(100) | NO | — | — | Nombre del administrador |
| 6 | `password_hash` | VARCHAR(256) | NO | — | — | Contraseña hasheada en espera de confirmación |
| 7 | `verified` | BOOLEAN | SÍ | — | app: False | Bandera de éxito |
| 8 | `attempts` | INTEGER | SÍ | — | app: 0 | Contador de intentos de validación |
| 9 | `expires_at` | DATETIME | NO | — | — | Fecha y hora de expiración (TTL 15 min) |
| 10 | `created_at` | DATETIME | SÍ | — | app: calculado | Fecha de solicitud |

---

#### 27. `verificacion_email_cliente` — CustomerEmailVerification

**Propósito:** Validación de correo electrónico para nuevos clientes del storefront online.

**Clave primaria:** `id` · **Campos:** 11 · **Foráneas:** 0 · **Índices:** 0 · **Únicos:** 0

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador único |
| 2 | `name` | VARCHAR(100) | NO | — | — | Nombre del cliente |
| 3 | `email` | VARCHAR(120) | NO | — | — | Correo a validar |
| 4 | `phone` | VARCHAR(20) | NO | — | — | Teléfono |
| 5 | `address` | VARCHAR(200) | SÍ | — | — | Dirección opcional |
| 6 | `password_hash` | VARCHAR(256) | NO | — | — | Clave hasheada |
| 7 | `code` | VARCHAR(10) | NO | — | — | Código OTP de 6 dígitos |
| 8 | `verified` | BOOLEAN | SÍ | — | app: False | Bandera de validación |
| 9 | `attempts` | INTEGER | SÍ | — | app: 0 | Intentos errados |
| 10 | `expires_at` | DATETIME | NO | — | — | Expiración del código |
| 11 | `created_at` | DATETIME | SÍ | — | app: calculado | Creación |

---

#### 28. `recuperacion_contrasena` — PasswordReset

**Propósito:** Tokens seguros con caducidad para el flujo de restablecimiento de contraseña olvidada.

**Clave primaria:** `id` · **Campos:** 6 · **Foráneas:** 1 · **Índices:** 0 · **Únicos:** 1

| # | Campo | Tipo | Nulo | Clave | Default | Descripción |
|---:|---|---|:--:|---|---|---|
| 1 | `id` | INTEGER | NO | PK | — | Identificador único |
| 2 | `user_id` | INTEGER | NO | FK → usuario.id | — | Usuario que solicitó el restablecimiento |
| 3 | `token` | VARCHAR(100) | NO | UQ | — | Token criptográfico unívoco de 64 caracteres |
| 4 | `expires_at` | DATETIME | NO | — | — | Expiración (1 hora) |
| 5 | `used` | BOOLEAN | SÍ | — | app: False | Si el enlace ya fue consumido |
| 6 | `created_at` | DATETIME | SÍ | — | app: calculado | Fecha de generación |

**Restricciones y accesos:**

- FK `user_id` → `usuario.id`
- UNIQUE (`token`)

---

## 3. Matriz de relaciones (claves foráneas)

| # | Tabla origen | Campo | Tabla destino | Campo destino | ON DELETE |
|---:|---|---|---|---|---|
| 1 | `configuracion_tienda` | `store_id` | `tienda` | `id` | — |
| 2 | `usuario` | `store_id` | `tienda` | `id` | — |
| 3 | `auditoria` | `user_id` | `usuario` | `id` | — |
| 4 | `recuperacion_contrasena` | `user_id` | `usuario` | `id` | — |
| 5 | `categoria` | `store_id` | `tienda` | `id` | — |
| 6 | `subcategoria` | `store_id` | `tienda` | `id` | — |
| 7 | `subcategoria` | `category_id` | `categoria` | `id` | — |
| 8 | `producto` | `store_id` | `tienda` | `id` | — |
| 9 | `producto` | `category_id` | `categoria` | `id` | — |
| 10 | `producto` | `subcategory_id` | `subcategoria` | `id` | — |
| 11 | `sesion_caja` | `store_id` | `tienda` | `id` | — |
| 12 | `sesion_caja` | `user_id` | `usuario` | `id` | — |
| 13 | `venta` | `store_id` | `tienda` | `id` | — |
| 14 | `venta` | `cash_session_id` | `sesion_caja` | `id` | — |
| 15 | `venta` | `credit_client_id` | `cliente_credito` | `id` | — |
| 16 | `venta` | `user_id` | `usuario` | `id` | — |
| 17 | `detalle_venta` | `sale_id` | `venta` | `id` | — |
| 18 | `detalle_venta` | `product_id` | `producto` | `id` | — |
| 19 | `cliente_credito` | `store_id` | `tienda` | `id` | — |
| 20 | `venta_credito` | `client_id` | `cliente_credito` | `id` | — |
| 21 | `venta_credito` | `sale_id` | `venta` | `id` | — |
| 22 | `pago_credito` | `client_id` | `cliente_credito` | `id` | — |
| 23 | `pedido` | `store_id` | `tienda` | `id` | — |
| 24 | `pedido` | `customer_id` | `cliente` | `id` | — |
| 25 | `pedido` | `user_id` | `usuario` | `id` | — |
| 26 | `pedido` | `sale_id` | `venta` | `id` | — |
| 27 | `detalle_pedido` | `order_id` | `pedido` | `id` | — |
| 28 | `detalle_pedido` | `product_id` | `producto` | `id` | — |
| 29 | `notificacion_pedido` | `order_id` | `pedido` | `id` | — |
| 30 | `proveedor` | `store_id` | `tienda` | `id` | — |
| 31 | `entrega_proveedor` | `supplier_id` | `proveedor` | `id` | — |
| 32 | `entrega_proveedor` | `store_id` | `tienda` | `id` | — |
| 33 | `entrega_proveedor` | `cash_session_id` | `sesion_caja` | `id` | — |
| 34 | `orden_compra` | `store_id` | `tienda` | `id` | — |
| 35 | `orden_compra` | `supplier_id` | `proveedor` | `id` | — |
| 36 | `orden_compra_item` | `order_id` | `orden_compra` | `id` | — |
| 37 | `orden_compra_item` | `product_id` | `producto` | `id` | — |
| 38 | `factura_proveedor` | `store_id` | `tienda` | `id` | — |
| 39 | `factura_proveedor` | `supplier_id` | `proveedor` | `id` | — |

---

## 4. Convenciones de tipos

| Tipo lógico | SQLAlchemy | SQLite | MySQL 8.0 | Uso en MercAPP |
|---|---|---|---|---|
| Entero | `Integer` | INTEGER | INT | IDs, cantidades y dinero en COP |
| Decimal | `Float` | REAL | DOUBLE | Cantidades por peso en pedidos web |
| Texto corto | `String(n)` | VARCHAR(n) | VARCHAR(n) | Nombres, correos y estados |
| Texto largo | `Text` | TEXT | TEXT | Mensajes, notas y HTML de correo |
| Booleano | `Boolean` | BOOLEAN (0/1) | TINYINT(1) | Banderas de estado |
| Fecha y hora | `DateTime` | DATETIME (texto ISO) | DATETIME | Marcas de tiempo |

**Convenciones del modelo:**

- Los valores monetarios se almacenan como **enteros en pesos colombianos (COP)**, sin centavos.
- Las fechas se generan en la aplicación (`datetime.now`) con `default`, no con `DEFAULT` en la base.
- Los nombres de tabla están en español y en singular; los de columna, en inglés.
- No se declaran `ON DELETE` ni `ON UPDATE`: la integridad se gestiona en la capa de servicio.

---

## 5. Observaciones de diseño

1. Las 39 claves foráneas carecen de reglas ON DELETE: borrar una entidad con historial exige limpieza manual o de la capa de servicio.
2. No existen restricciones CHECK; reglas como stock no negativo o montos positivos se validan en servicios y en los procedimientos de MySQL.
3. configuracion_tienda concentra 30 columnas (fiscales, hardware y tema visual); es la candidata natural a normalizar.
4. usuario.email es único global: un mismo correo no puede operar en dos tiendas distintas.
5. producto.barcode está indexado pero no es único; la unicidad se valida en la aplicación.
6. auditoria no tiene política de retención ni particionado por fecha, por lo que crece indefinidamente.
7. Las tres tablas de verificación almacenan el hash de la contraseña antes de confirmar la cuenta y requieren purga de códigos expirados.
8. Las fotos de factura se copian a uploads/invoices y a static/images/invoices, lo que puede desincronizarse.

### 5.1. Claves foráneas sin índice explícito (30)

| Tabla | Campo FK | Referencia |
|---|---|---|
| `configuracion_tienda` | `store_id` | `tienda.id` |
| `usuario` | `store_id` | `tienda.id` |
| `auditoria` | `user_id` | `usuario.id` |
| `recuperacion_contrasena` | `user_id` | `usuario.id` |
| `producto` | `subcategory_id` | `subcategoria.id` |
| `sesion_caja` | `user_id` | `usuario.id` |
| `venta` | `credit_client_id` | `cliente_credito.id` |
| `venta` | `user_id` | `usuario.id` |
| `detalle_venta` | `sale_id` | `venta.id` |
| `detalle_venta` | `product_id` | `producto.id` |
| `cliente_credito` | `store_id` | `tienda.id` |
| `venta_credito` | `client_id` | `cliente_credito.id` |
| `venta_credito` | `sale_id` | `venta.id` |
| `pago_credito` | `client_id` | `cliente_credito.id` |
| `pedido` | `customer_id` | `cliente.id` |
| `pedido` | `user_id` | `usuario.id` |
| `pedido` | `sale_id` | `venta.id` |
| `detalle_pedido` | `order_id` | `pedido.id` |
| `detalle_pedido` | `product_id` | `producto.id` |
| `notificacion_pedido` | `order_id` | `pedido.id` |
| `proveedor` | `store_id` | `tienda.id` |
| `entrega_proveedor` | `supplier_id` | `proveedor.id` |
| `entrega_proveedor` | `store_id` | `tienda.id` |
| `entrega_proveedor` | `cash_session_id` | `sesion_caja.id` |
| `orden_compra` | `store_id` | `tienda.id` |
| `orden_compra` | `supplier_id` | `proveedor.id` |
| `orden_compra_item` | `order_id` | `orden_compra.id` |
| `orden_compra_item` | `product_id` | `producto.id` |
| `factura_proveedor` | `store_id` | `tienda.id` |
| `factura_proveedor` | `supplier_id` | `proveedor.id` |

> **Nota:** MySQL/InnoDB crea automáticamente un índice por cada clave foránea, de modo que en
> producción estas columnas sí quedan indexadas. SQLite no lo hace: si se consultan esas columnas
> en local conviene declarar `index=True` explícitamente en el modelo.

---

## 6. Glosario de estados

| Tabla | Campo | Valores posibles |
|---|---|---|
| `usuario` | `status` | `ACTIVO`, `BLOQUEADO` |
| `sesion_caja` | `status` | `abierta`, `cerrada` |
| `venta` | `status` | `completada`, `anulada` |
| `venta` | `payment_method` | `efectivo`, `tarjeta`, `transferencia`, `fiado`, `mixto` |
| `venta_credito` | `status` | `pendiente`, `pagado` |
| `pedido` | `status` | `pendiente`, `en_preparacion`, `en_camino`, `entregado`, `cancelado` |
| `pedido` | `order_type` | `domicilio`, `recoger_tienda` |
| `orden_compra` | `status` | `PENDIENTE`, `CONFIRMADA`, `EN_CAMINO`, `ENTREGADA`, `CANCELADA` |
| `factura_proveedor` | `status` | `PENDIENTE`, `PAGADA_PARCIAL`, `PAGADA` |
| `entrega_proveedor` | `payment_method` | `efectivo_caja`, `transferencia`, `credito`, `mixto` |
| `proveedor` | `status` | `ACTIVO`, `SUSPENDIDO` |
| `cola_correos` | `status` | `pending`, `sent`, `failed` |
| `auditoria` | `severity` | `INFO`, `WARNING`, `CRITICAL` |

---

*Documento generado desde el código fuente del repositorio `MercAPP_IS2_Backend`.*
