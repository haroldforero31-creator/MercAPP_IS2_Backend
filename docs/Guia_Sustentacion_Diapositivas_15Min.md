# GUÍA ESTRATÉGICA DE SUSTENTACIÓN — MercAPP POS
**Guion Paso a Paso, Explicación de Conceptos Clave y Respuestas a Preguntas del Docente**

---

## ⏱️ 1. Distribución del Tiempo (15 Minutos Exactos)

| Minuto | Tema Central | Qué Mostrar en Pantalla | Quién Expone |
| :---: | :--- | :--- | :---: |
| **0:00 - 2:30** | **Pitch y Propuesta de Valor:** Problema de las tiendas de barrio, mercado y solución. | Diapositivas 1 y 2 + Código QR activo. | Integrante 1 |
| **2:30 - 7:30** | **Live Demo (Demostración en Vivo):** Flujo de los 4 roles reales en producción. | Navegador web en `https://mercapp-deploy.onrender.com`. | Integrante 2 y 3 |
| **7:30 - 11:30** | **Arquitectura Técnica, BD y Seguridad:** Capas, 28 tablas, SPs/Triggers, JWT/CORS. | Diapositivas 4, 5, 6 y código de GitHub. | Integrante 3 y 4 |
| **11:30 - 13:30** | **Calidad de Software, CI y SonarCloud:** 37 tests, 69% cobertura, pipeline y fixes. | GitHub Actions (.github/ci.yml) y SonarCloud. | Integrante 4 |
| **13:30 - 15:00** | **Conclusiones y Ronda de Preguntas:** Respuestas técnicas preparadas. | Diapositiva final con métricas y enlaces. | Todos |

---

## 💡 2. Guía de Conceptos Técnicos para el Equipo (Para Explicar con Solvencia)

> [!TIP]
> Si hicieron "vibe coding", no se preocupen. Estos son los conceptos exactos que deben dominar para hablar con el vocabulario técnico que el docente espera:

### A. ¿Qué tecnologías usamos y por qué?
- **Python y Flask:** Elegimos Flask porque es un microframework ligero y altamente extensible. A diferencia de Django (que impone su propio ORM y estructura rígida), Flask nos permitió construir una arquitectura limpia por capas (Controllers, Services, Repositories).
- **SQLAlchemy 2.0:** Es el ORM (Object-Relational Mapping) líder de Python. Mapea clases de Python a tablas SQL. Usamos la sintaxis moderna `db.session.get(Modelo, id)` que previene consultas redundantes y reemplaza la API obsoleta `query.get()`.
- **Waitress vs Gunicorn:** Usamos **Waitress** para el ejecutable de escritorio en Windows porque es un servidor WSGI nativo multihilo que no depende del comando `fork()` de Unix. Para el despliegue en la nube (Render / Linux), usamos **Gunicorn** con 2 workers.
- **SQLite WAL vs TiDB Cloud:** En local usamos SQLite con modo **WAL (Write-Ahead Logging)**, lo que permite que múltiples hilos lean y escriban simultáneamente sin bloquear la base de datos. En la nube usamos **TiDB Cloud Serverless**, que es compatible con el protocolo MySQL 8.0 y escala el almacenamiento de forma distribuida.

### B. ¿Cómo funciona la API y la autenticación híbrida?
- **Doble autenticación:**
  1. *Sesión Web (Navegador):* Cuando el cajero o administrador entra por la web, el servidor guarda una cookie `session` firmada criptográficamente con `HttpOnly` (para evitar que JavaScript malicioso la lea) y `SameSite=Lax` (para mitigar CSRF).
  2. *API Stateless JWT (Clientes desacoplados / Postman):* Para clientes externos o móviles, creamos el endpoint `POST /api/auth/token`. Este endpoint emite un token Bearer firmado con algoritmo HS256 (`PyJWT`).
  3. *Interceptor `@app.before_request`:* Revisa si la petición incluye el encabezado `Authorization: Bearer <token>`. Si es válido, autentica la petición de forma stateless sin necesidad de cookies.

### C. ¿Qué pasa con los Stored Procedures y Triggers? (Pregunta Clave del Docente)
- **La respuesta correcta:**  
  *"Profesor, MercAPP cuenta con un script DDL oficial (`database/stored_procedures_triggers.sql`) con los 5 Stored Procedures y 5 Triggers en sintaxis estándar de MySQL 8.0+. Sin embargo, como en entornos modernos de nube serverless (como TiDB Cloud) y motores embebidos (SQLite WAL) los motores distribuidos delegan la lógica procedimental a la capa de cómputo para no generar cuellos de botella en el almacenamiento, diseñamos el servicio `DatabaseRoutinesService` (`services/database_routines_service.py`) en Python. Esto nos permite ejecutar exactamente la misma lógica de los 5 SPs y 5 Triggers con atomicidad transaccional y validarla al 100% en nuestras pruebas automatizadas de integración."*

---

## 🖥️ 3. Guion de Diapositivas (10 Slides)

### Slide 1: Portada y Enlace en Vivo
- **Título:** MercAPP POS — Sistema Inteligente de Punto de Venta y Gestión Retail.
- **Subtítulo:** Sustentación Proyecto de Aula — Ingeniería de Software II.
- **Contenido:** Nombres de los 4 integrantes, logo y **Código QR grande** hacia `https://mercapp-deploy.onrender.com`.

### Slide 2: El Problema del Comercio Minorista
- 78% de tiendas de barrio pierden dinero por la libreta de fiados en papel.
- Hurtos hormiga o descuadres por falta de arqueos de caja ciegos.
- Sin canal digital para recibir pedidos frente a cadenas como D1 o Ara.
- Rupturas de stock por falta de alertas preventivas de reorden.

### Slide 3: La Solución Integral MercAPP
- 4 Roles reales: Administrador, Cajero, Cliente Digital y Proveedor B2B.
- POS rápido con soporte de escáner y productos por peso (báscula).
- Libreta digital de crédito con límites y cálculo de morosidad.
- Asistente de Inteligencia Artificial (Merki) con consultas en lenguaje natural.

### Slide 4: Live Demo (Demostración en Vivo en Producción)
- **Paso 1:** Cajero abre turno con base de \$50.000.
- **Paso 2:** Venta rápida en POS (un producto escaneado + un producto por peso). Pago en efectivo con vuelto automático.
- **Paso 3:** Admin consulta a Merki: *"¿Cuánto vendí hoy?"* y descarga el **Reporte en Excel** con formato corporativo.
- **Paso 4:** Cliente entra a `/customer/login` y hace un pedido en línea.
- **Paso 5:** Proveedor entra a `/proveedor/login` y sube factura digital de entrega.
- **Paso 6:** Cajero realiza el **Arqueo Ciego** y cierra turno.

### Slide 5: Arquitectura de Software N-Capas
- Diagrama de capas: Presentación ➔ Controladores ➔ DTOs ➔ Servicios ➔ Repositorios ➔ Modelos ➔ Base de Datos.
- Separación de responsabilidades (SRP), alta cohesión y testeabilidad aislada.

### Slide 6: Base de Datos Relacional y Rutinas
- **28 Tablas relacionales** en tercera forma normal (3NF).
- **5 Stored Procedures:** `sp_registrar_venta_pos`, `sp_cerrar_turno_caja`, `sp_reporte_ventas_diarias`, `sp_abonar_deuda_cliente`, `sp_reorden_stock_minimo`.
- **5 Triggers:** Auditoría de precios, prevención de stock negativo, registro de venta, amortización de crédito y protección contra borrado de usuarios.
- Implementación dual: Script MySQL 8.0+ y capa `DatabaseRoutinesService` para portabilidad TiDB/SQLite.

### Slide 7: Seguridad y Mitigación de Vulnerabilidades
- **Bloqueo temporal de 15 minutos:** Campo `locked_until` en base de datos; tras 5 intentos fallidos se suspende y se auto-desbloquea tras cumplirse el plazo.
- **CORS Restringido:** No refleja credenciales para orígenes comodín (`supports_credentials=False`).
- **CSRF Inteligente:** Obligatorio en sesión web; exento dinámicamente si la petición porta un Bearer JWT válido.
- **Cabeceras HTTP:** `Content-Security-Policy (CSP)`, `X-Frame-Options: SAMEORIGIN`, `nosniff`.
- **Anti-Open Redirect:** Función `sanitize_next_url()` en `utilities/security.py`.

### Slide 8: Calidad de Software y Suite Automatizada
- **37 Pruebas Automatizadas:** 100% de tasa de éxito (0 fallos).
- **69% de Cobertura de Código Verificada** en el CI sobre todos los módulos críticos.
- Prueba de estrés con 500 peticiones concurrentes a 206.8 RPS y prueba de sobreventa atómica (0 race conditions).

### Slide 9: CI/CD y Análisis Estático en SonarCloud
- **GitHub Actions (`.github/workflows/ci.yml`):** Pruebas en Python 3.11 y 3.12 con Quality Gate que falla si la cobertura desciende del 68%.
- **SonarCloud:** Reducción comprobada de deuda técnica con 4 correcciones individuales firmadas por cada integrante.

### Slide 10: Conclusiones
- MercAPP es una solución lista para producción que combina solidez arquitectónica, seguridad integral y facilidad de uso para el tendero.
- 100% de los 11 criterios cumplidos y demostrados en vivo.

---

## 🎯 4. Respuestas a Preguntas Trampa del Docente

> **P: "¿Por qué no usan Redis para el Rate Limiting?"**  
> *R:* "Para el contexto de despliegue en tiendas de barrio (que pueden operar en modo standalone local en una mini-PC sin internet), agregar un servidor Redis aumentaría innecesariamente la complejidad y el consumo de memoria. Nuestro módulo `InMemoryRateLimiter` utiliza el algoritmo de ventana deslizante con `threading.Lock`, ofreciendo protección thread-safe en microsegundos sin dependencias externas."

> **P: "¿Por qué hay 28 tablas si al inicio se mencionaban menos?"**  
> *R:* "Porque MercAPP cubre el ciclo de vida completo del negocio: no solo ventas e inventario, sino también la gestión de fiados y clientes de crédito (3 tablas), el portal B2B de proveedores con facturas digitales (5 tablas), la cola asíncrona de correos resiliente a desconexiones (cola_correos) y la trazabilidad de auditoría de seguridad."

> **P: "¿Cómo demuestran que la concurrencia no genera sobreventa?"**  
> *R:* "Diseñamos una prueba de estrés multihilo (`tests/stress_test_500.py`) que lanza 30 hilos concurrentes intentando comprar simultáneamente un producto con stock inicial de 10 unidades. Gracias a la transacción atómica con validación previa en `DatabaseRoutinesService` y el modo WAL de SQLite, exactamente 10 hilos completaron la venta y 20 recibieron el error de 'Stock insuficiente', dejando el stock final exactamente en 0."
