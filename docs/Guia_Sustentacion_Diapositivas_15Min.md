# GUÍA ESTRATÉGICA DE SUSTENTACIÓN — MercAPP POS
**Estructura de Diapositivas, Tiempos, Guion de Exposición y Respuestas a Preguntas Técnicas**

---

## ⏱️ 1. Distribución del Tiempo (15 Minutos Exactos)

| Bloque | Minutos | Temática Central | Expositor Sugerido |
| :---: | :---: | :--- | :--- |
| **Bloque 1** | **0:00 - 3:00** | **Pitch de Negocio:** Problema, Propuesta de Valor y Mercado Objetivo | Integrante 1 (Líder / Product Owner) |
| **Bloque 2** | **3:00 - 8:00** | **Live Demo (Demostración en Vivo):** Flujo real de los 4 Roles | Integrante 2 y 3 (Operaciones / Front-End) |
| **Bloque 3** | **8:00 - 11:30** | **Arquitectura Técnica, BD y Seguridad:** N-Capas, 5 SPs, 5 Triggers, JWT y Concurrencia | Integrante 3 y 4 (Arquitecto / Backend) |
| **Bloque 4** | **11:30 - 13:30** | **Calidad de Software, CI/CD y SonarCloud:** Tests 100%, Cobertura y Pipeline GitHub | Integrante 4 (QA / DevOps) |
| **Bloque 5** | **13:30 - 15:00** | **Conclusiones, Impacto y Cierre:** Ronda de Preguntas del Docente | Todo el equipo |

---

## 🖥️ 2. Estructura de las Diapositivas (Slide by Slide)

### Diapositiva 1: Portada y Presentación
- **Título:** MercAPP POS — Sistema Inteligente de Punto de Venta, Gestión de Inventario y Relación B2B/B2C.
- **Subtítulo:** Proyecto de Aula — Ingeniería de Software II.
- **Elementos Clave:**
  - Nombres completos y códigos de los 4 integrantes.
  - **Código QR grande** enlazado a la aplicación en vivo en Render (`https://mercapp-pos.onrender.com`).
  - Logos institucionales.

### Diapositiva 2: El Problema en el Comercio Minorista
- **Puntos Clave:**
  1. *Pérdida en la libreta de fiados:* El 78% de tiendas de barrio pierde dinero por falta de control en ventas a crédito o clientes que superan su capacidad de pago.
  2. *Descuadre y manipulación de caja:* Hurtos hormiga o errores humanos al no realizar arqueos ciegos.
  3. *Aislamiento digital:* Tiendas sin canal de venta online frente a grandes cadenas (D1, Ara, Éxito).
  4. *Rupturas de stock:* Falta de comunicación oportuna con proveedores.

### Diapositiva 3: La Solución — MercAPP
- **Propuesta de Valor:** Un ecosistema integral de 4 roles que no requiere hardware costoso y funciona en la nube o local:
  - POS ultrarrápido con báscula y código de barras.
  - Asistente IA "Merki" para toma de decisiones sin reportes complicados.
  - Libreta digital de fiados con límites de crédito.
  - Portal para pedidos de clientes y portal B2B para entregas de proveedores.

### Diapositiva 4: Demostración en Vivo (Flujo de los 4 Roles)
*(En este momento se comparte pantalla con la app ejecutándose)*
- **Paso 1 (Cajero):** Apertura de turno con base de \$50.000. Venta rápida de un producto por unidad (escáner) y un producto por peso en báscula (ej. 1.5 kg de queso). Pago con \$50.000 y cálculo de vuelto en pantalla.
- **Paso 2 (Admin):** Entra al Dashboard. Muestra cómo Merki responde en 1 segundo *"¿Cuánto vendí hoy?"*. Descarga el **Reporte en Excel** profesional con paleta esmeralda y fórmulas de suma.
- **Paso 3 (Cliente):** Abre el portal `/customer/login`, agrega productos al carrito y genera un pedido en línea.
- **Paso 4 (Proveedor):** Entra a `/proveedor/login`, registra una entrega de mercancía y adjunta la factura digital.
- **Paso 5 (Cajero):** Realiza el **Arqueo Ciego** de caja y cierra el turno.

### Diapositiva 5: Arquitectura de Software N-Capas
- **Diagrama Mermaid de Capas:**
  - Presentación (Jinja2 + JS Vanilla ES6) ➔ Controladores (Blueprints) ➔ DTOs (Data Transfer Objects) ➔ Lógica de Negocio (Services) ➔ Persistencia (Repositories) ➔ Modelos (SQLAlchemy) ➔ Base de Datos (TiDB Cloud / SQLite WAL).
- **Justificación:** Alta cohesión, bajo acoplamiento, testeabilidad independiente de servicios sin levantar servidor web y extensibilidad para clientes móviles futuros.

### Diapositiva 6: Base de Datos Empresarial (Stored Procedures y Triggers)
- **18 Tablas Relacionales en 3NF.**
- **5 Procedimientos Almacenados:**
  1. `sp_registrar_venta_pos`: Transacción atómica venta + descuento de stock.
  2. `sp_cerrar_turno_caja`: Consolidación y balance de caja.
  3. `sp_reporte_ventas_diarias`: Resumen analítico por categorías.
  4. `sp_abonar_deuda_cliente`: Amortización de fiados y cambio de estado a PAGADA.
  5. `sp_reorden_stock_minimo`: Detección preventiva de quiebres de inventario.
- **5 Triggers de Integridad y Auditoría:**
  1. `trg_auditoria_cambio_precio`: Historial ante modificaciones de precios.
  2. `trg_evitar_stock_negativo`: Excepción `SIGNAL SQLSTATE '45000'` si el stock cae de 0.
  3. `trg_auditoria_nueva_venta`: Trazabilidad de facturación.
  4. `trg_actualizar_saldo_credito`: Descuento automático de saldo con cada abono.
  5. `trg_auditoria_eliminar_usuario`: Protección contra borrado de registros históricos.

### Diapositiva 7: Seguridad, Autenticación y API Desacoplada
- **Doble Esquema de Autenticación:**
  - *Sesión Web Stateful:* Cookies seguras con flags `HttpOnly` y `SameSite`.
  - *API Stateless JWT:* Emisión de tokens Bearer en `/api/auth/token` y políticas **CORS** explícitas para clientes externos.
- **Defensas de Seguridad:**
  - Protección CSRF global en todos los formularios y llamadas asíncronas.
  - Sanitización anti-XSS en el POS.
  - Rate Limiting (429 Too Many Requests) y bloqueo temporal tras 5 intentos fallidos de login.
  - Hashing criptográfico moderno con Werkzeug (`scrypt` / `pbkdf2:sha256`).
- **Documentación de API:** Colección de Postman v2.1 completa con tests automáticos de respuesta.

### Diapositiva 8: Pruebas Automatizadas y Calidad de Código
- **Resultados de la Suite Automatizada:**
  - **33 Pruebas Automatizadas:** 100% de tasa de éxito (0 fallos).
  - Cobertura de código superior al **68%** en los módulos críticos (Modelos 95%, Servicios 85%, Controladores 75%, Reportes 100%).
- **Prueba de Estrés y Concurrencia:**
  - 500 peticiones concurrentes a 206.8 RPS con p95 de 1001 ms sin caídas de servidor gracias a Waitress multihilo y SQLite en modo WAL.
  - Simulación de sobreventa con 30 hilos simultáneos: 10 ventas confirmadas, 20 rechazos limpios, stock final exactamente 0 (0 race conditions).

### Diapositiva 9: Pipeline de Integración Continua (CI/CD) y SonarCloud
- **GitHub Actions (`.github/workflows/ci.yml`):**
  - Pruebas automáticas ejecutadas en Python 3.11 y 3.12 con cada `push` y `pull_request`.
- **Análisis de Deuda Técnica (SonarCloud):**
  - Demostración del escaneo inicial vs. escaneo final.
  - Distribución de resolución de incidencias entre los 4 integrantes del equipo (Security Hotspots, Code Smells, Bugs).

### Diapositiva 10: Conclusiones y Lecciones Aprendidas
- **Impacto Real:** MercAPP no es un prototipo escolar; es un sistema robusto, con arquitectura por capas, seguro contra ataques reales y preparado para producción en la nube.
- **Cumplimiento Académico:** 100% de los 11 criterios cumplidos y documentados.
- **Agradecimientos:** Espacio para preguntas del docente y del auditorio.

---

## 🎯 3. Respuestas Preparadas a Preguntas Técnicas del Docente

> **P1: "¿Por qué utilizaron una arquitectura por capas en lugar de dejar el código en `app.py`?"**  
> *Respuesta:* Para garantizar el principio de responsabilidad única (SRP) y alta mantenibilidad. Separar en Controladores, Servicios y Repositorios nos permitió escribir pruebas unitarias sobre las reglas de negocio (ej. calcular cambio o verificar cupo de crédito) en milisegundos sin necesidad de levantar el servidor web ni simular clientes HTTP. Además, desacoplar el acceso a datos en repositorios nos permite alternar con total transparencia entre SQLite para uso local y TiDB Cloud para despliegue en la nube.

> **P2: "¿Cómo evitaron condiciones de carrera (Race Conditions) y sobreventas si 2 cajeros venden el último producto al mismo tiempo?"**  
> *Respuesta:* Lo resolvimos a doble nivel:  
> 1. En la base de datos a través de una transacción atómica con el Stored Procedure `sp_registrar_venta_pos`, reforzado con el Trigger `trg_evitar_stock_negativo` que lanza un error `SIGNAL SQLSTATE '45000'` si el stock resultante es negativo.  
> 2. En el servidor mediante SQLite en modo WAL (Write-Ahead Logging) y el motor multihilo de Waitress. Lo comprobamos experimentalmente con nuestra prueba de estrés (`tests/stress_test_500.py`), lanzando 30 hilos simultáneos sobre un producto con 10 unidades: el sistema aprobó exactamente 10 ventas y rechazó 20 con mensaje de stock insuficiente.

> **P3: "¿Cómo conviven la autenticación por sesión web y la autenticación JWT en una misma aplicación?"**  
> *Respuesta:* Diseñamos un modelo híbrido en [app.py](file:///c:/Users/USUARIO/Pictures/MercAPP_IS2_Backend/app.py). Para la interfaz web (cajeros y administradores navegando en Jinja2), usamos Flask-Login con cookies de sesión protegidas por `HttpOnly` y `SameSite`. Para clientes desacoplados o externos, creamos el endpoint `POST /api/auth/token` que emite un token JWT firmado. Luego, implementamos un interceptor `@app.before_request`: si la petición incluye la cabecera `Authorization: Bearer <token>`, el interceptor decodifica el token con `PyJWT`, verifica la firma criptográfica y autentica al usuario en el contexto de la petición, permitiendo un consumo REST puro sin cookies.

> **P4: "¿Qué vulnerabilidades encontraron en el código y cómo las solucionaron?"**  
> *Respuesta:* Durante nuestra auditoría identificamos y subsanamos fallos críticos (P0 y P1):  
> - Faltaban tokens CSRF en formularios de login y proveedor, lo que provocaba errores 400 o dejaba expuestas peticiones forjadas; se integró `CSRFProtect` con tokens ocultos y cabeceras `X-CSRFToken` en peticiones Fetch.  
> - El asistente Merki y la API de productos aceptaban `store_id` desde el payload de clientes anónimos; se forzó el decorador `@login_required` y la asignación estricta de `store_id = current_user.store_id`.  
> - El enlace de reseteo de contraseña se imprimía en los mensajes flash de la pantalla; se eliminó del flash y se encapsuló en envíos exclusivos por correo SMTP.  
> - Se implementaron cabeceras HTTP de seguridad (`X-Frame-Options`, `X-Content-Type-Options`, `CSP`) y limitación de tasa (Rate Limiting) para prevenir ataques de fuerza bruta.
