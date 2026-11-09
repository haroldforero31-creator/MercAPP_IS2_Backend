# MANUAL DE USUARIO — MercAPP POS
**Guía Operativa Integral para los 4 Roles del Sistema**

---

## 1. Introducción y Acceso al Sistema

MercAPP es una plataforma integral de gestión para tiendas de abarrotes, minimercados y supermercados independientes. Ofrece una experiencia moderna, rápida e intuitiva que conecta el punto de venta (POS) físico con la administración, los pedidos en línea de los clientes y el aprovisionamiento de proveedores.

### 1.1. URLs de Acceso Principal (Producción en Vivo)
- **Portal Administrativo y POS (Admin / Cajero):** [https://mercapp-deploy.onrender.com/login](https://mercapp-deploy.onrender.com/login)
- **Portal de Clientes (Catálogo y Pedidos Online):** [https://mercapp-deploy.onrender.com/customer/login](https://mercapp-deploy.onrender.com/customer/login)
- **Portal de Proveedores (Órdenes y Entregas B2B):** [https://mercapp-deploy.onrender.com/proveedor/login](https://mercapp-deploy.onrender.com/proveedor/login)
- **Entorno Local de Desarrollo:** `http://localhost:5000/login`

---

## 2. Matriz de Permisos y Capacidades por Rol (CRUD)

| Módulo / Funcionalidad | Rol 1: Administrador | Rol 2: Cajero | Rol 3: Cliente Digital | Rol 4: Proveedor |
| :--- | :---: | :---: | :---: | :---: |
| **Inicio de Sesión y Perfil** | Acceso a `/login` con 2FA opcional | Acceso a `/login` en modo POS | Registro y acceso en `/customer/login` | Registro y acceso en `/proveedor/login` |
| **Catálogo de Productos** | **CRUD Total** (Crear, Editar, Precios, Eliminar) | **Lectura** (Búsqueda y Escáner) | **Lectura** (Ver disponibles y precios) | **Lectura** (Productos que abastece) |
| **Venta en POS** | Total (Crear, Anular, Ver historial) | **Crear Ventas y Cobro** | Sin acceso | Sin acceso |
| **Turnos y Arqueo de Caja** | Ver todos los arqueos y diferencias | **Apertura de turno y Arqueo Ciego** | Sin acceso | Sin acceso |
| **Clientes y Fiados** | **CRUD** (Asignar cupo, registrar abonos) | Registrar venta fiada a clientes autorizados | Consultar pedidos propios | Sin acceso |
| **Pedidos en Línea** | Cambiar estado (Preparación, Despacho) | Consultar pedidos para entrega | **Crear pedidos y Carrito virtual** | Sin acceso |
| **Entregas de Mercancía** | **Aprobar entrega y salida de caja** | Sin acceso | Sin acceso | **Registrar entrega y subir factura** |
| **Reportes Excel (.xlsx)** | Descargar ventas e inventario valorizado | Sin acceso | Sin acceso | Sin acceso |
| **Asistente Merki (IA)** | Consultas de negocio y caja | Consultas rápidas de turno | Sin acceso | Sin acceso |

---

## 3. Rol 1: Administrador de Tienda

El Administrador tiene control total sobre las operaciones, el personal, los inventarios, la tesorería y la configuración del negocio.

### 3.1. Gestión de Productos y Precios
1. Ingrese al menú lateral y seleccione **Productos**.
2. **Nuevo Producto:** Presione el botón `+ Nuevo Producto`.
   - Ingrese el nombre comercial del artículo.
   - Seleccione la categoría correspondiente.
   - Ingrese el precio de venta en pesos colombianos ($ COP).
   - Defina el tipo de venta: **Por Unidad** o **Por Peso (Báscula)** especificando si se comercializa en kilogramos o gramos.
   - Escanee o asigne un **Código de Barras** único.
   - Establezca el stock disponible y el nivel de **Stock Mínimo** para alertas de reorden.
3. **Auditoría de Precios:** Al cambiar el precio de un producto, el sistema genera automáticamente un registro en el módulo de auditoría indicando fecha, usuario responsable, precio anterior y precio nuevo.

### 3.2. Gestión de Cajeros y Seguridad de Cuentas
1. Diríjase a **Configuración > Cajeros**.
2. Para dar de alta a un cajero, ingrese su nombre, correo electrónico y contraseña.
3. **Bloqueo Temporal de 15 Minutos:** Si un cajero o administrador ingresa 5 contraseñas erróneas consecutivas, el sistema suspende temporalmente el acceso durante 15 minutos mediante el campo `locked_until`. Al cumplirse el plazo, el sistema realiza el auto-desbloqueo de forma transparente sin requerir reinicio del servidor.

### 3.3. Control de Deudas y Clientes de Crédito (Fiados)
1. Ingrese a **Clientes de Crédito**.
2. Registre los datos del cliente: Nombre completo, teléfono, correo y **Cupo Máximo Autorizado** de crédito.
3. Desde esta pantalla puede:
   - Consultar el historial detallado de compras fiadas.
   - Registrar **Abonos Parciales o Totales** en efectivo o transferencia.
   - El sistema calcula automáticamente la morosidad y alerta si el cliente supera su límite de endeudamiento.

### 3.4. Descarga de Reportes Ejecutivos en Excel (.xlsx)
1. En la barra superior o sección de reportes, seleccione:
   - **Reporte de Ventas en Excel (`/api/reports/sales`):** Archivo con formato corporativo, paleta esmeralda, desglosado por recibo, método de pago, cajero y fórmulas de totalización automática `SUM()`.
   - **Reporte de Inventario en Excel (`/api/reports/inventory`):** Relación valorizada de todo el inventario activo clasificado por categoría con semáforo de existencias (OK, Bajo, Crítico).

### 3.5. Asistente con Inteligencia Artificial "Merki"
1. Haga clic en el botón flotante de **Merki** en la esquina inferior del sistema.
2. Formule preguntas en lenguaje natural como:
   - *"¿Cuánto vendí hoy?"*
   - *"¿Cómo está la caja en este turno?"*
   - *"¿Qué productos están por agotarse?"*
   - *"¿Quién me debe más dinero en fiados?"*
   - *"¿Cuáles son los productos más vendidos?"*
3. Merki analiza instantáneamente las tablas de la tienda y responde con resúmenes ejecutivos claros.

---

## 4. Rol 2: Operador de Caja (Cajero)

Diseñado para operar con máxima velocidad y sin distracciones, permitiendo atender clientes de forma fluida tanto con teclado físico como con pantalla táctil.

### 4.1. Apertura de Turno de Caja
1. Al iniciar la jornada, el cajero inicia sesión con sus credenciales.
2. El sistema solicita obligatoriamente el **Monto Base de Apertura** (efectivo inicial para dar cambio).
3. Una vez confirmada la base, se habilita la pantalla del POS.

### 4.2. Proceso de Venta en el POS
1. **Agregar Productos:**
   - **Por Escáner:** Pistolee el código de barras del producto; se agregará instantáneamente al carrito.
   - **Por Búsqueda Rápida:** Escriba las primeras letras del producto o presione sobre su tarjeta visual.
   - **Productos por Peso (Báscula):** Si el producto se vende por peso (ej. frutas, verduras, carnes), el sistema solicita el gramaje y calcula el precio exacto proporcional.
2. **Métodos de Pago:**
   - **Efectivo:** Ingrese el monto recibido; el sistema mostrará en números grandes el cambio exacto a devolver.
   - **Tarjeta / Transferencia:** Registre la confirmación del comprobante.
   - **Crédito / Fiado:** Seleccione el cliente registrado en la libreta digital; el sistema validará que la venta no exceda su cupo disponible.
3. **Comprobante de Venta:** Al confirmar, se genera el comprobante digital con código de barras y desglose de artículos.

### 4.3. Cierre de Turno y Arqueo Ciego
1. Al finalizar el turno, presione **Cerrar Turno**.
2. **Arqueo Ciego:** El cajero ingresa el recuento físico del dinero en gaveta sin que el sistema le revele el total teórico esperado (evitando manipulaciones).
3. El sistema registra el cierre y emite el resumen consolidado para el administrador.

---

## 5. Rol 3: Cliente Digital (`Customer`)

Permite a los vecinos y clientes habituales consultar el catálogo de su tienda y realizar pedidos para recoger en tienda o a domicilio.

### 5.1. Registro y Verificación
1. Ingrese a `/customer/login` y seleccione **Crear Cuenta**.
2. Ingrese su nombre, correo electrónico y contraseña.
3. El sistema envía un correo institucional con el logo corporativo y un código de verificación de 6 dígitos.

### 5.2. Catálogo y Pedidos Online
1. Inicie sesión para ver los productos disponibles con precios actualizados y fotos.
2. Agregue los productos al carrito virtual.
3. Seleccione el tipo de entrega (Recoger en tienda o Domicilio) e ingrese observaciones.
4. Confirme el pedido. Podrá seguir el estado en tiempo real:
   - `PENDIENTE` ➔ `EN PREPARACIÓN` ➔ `LISTO PARA ENTREGA` ➔ `ENTREGADO`.

---

## 6. Rol 4: Proveedor de Mercancía (`Supplier`)

Canal B2B que digitaliza la relación con los distribuidores y surtidores de mercancía.

### 6.1. Acceso al Portal de Proveedores
1. Ingrese a `/proveedor/login`.
2. Si es un nuevo proveedor, regístrese indicando razón social, NIT/Cédula, correo y teléfono.

### 6.2. Gestión de Entregas y Facturación
1. **Ver Órdenes de Compra:** Consulte las solicitudes de mercancía generadas automáticamente cuando el stock baja del mínimo.
2. **Registrar Entrega:** Cuando el repartidor llega al establecimiento:
   - Selecciona la tienda receptora.
   - Ingresa los productos entregados y las cantidades verificadas.
   - Carga la foto o PDF de la **Factura Digital**.
   - Si la entrega incluye cobro en efectivo, registra el monto cobrado; el sistema requerirá la aprobación expresa del administrador de la tienda para asentar la salida de caja.
3. **Historial de Pagos:** Consulta de facturas canceladas, pendientes de pago y recibos de entrega emitidos.
