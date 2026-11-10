# 📦 PAQUETE DE ENTREGA FINAL — MERCAPP POS
### Asignatura: Ingeniería de Software II (IS2) — Entrega y Sustentación Final

---

## 🌐 1. Enlaces Oficiales del Proyecto

| Recurso | Enlace / URL | Estado |
|---------|--------------|--------|
| 🚀 **Aplicación en Producción (Render)** | [https://mercapp-deploy.onrender.com](https://mercapp-deploy.onrender.com) | En Vivo (24/7) |
| 💻 **Descarga Directa Software POS Windows** | [https://mercapp-deploy.onrender.com/descargar-pos](https://mercapp-deploy.onrender.com/descargar-pos) | Archivo RAR (80.2 MB) |
| 🐙 **Repositorio Backend (API Flask)** | [https://github.com/haroldforero31-creator/MercAPP_IS2_Backend](https://github.com/haroldforero31-creator/MercAPP_IS2_Backend) | Público / CI Passing |
| 🎨 **Repositorio Frontend (Templates & UI)** | [https://github.com/haroldforero31-creator/MercAPP_IS2_Frontend](https://github.com/haroldforero31-creator/MercAPP_IS2_Frontend) | Público / Ramas sincronizadas |
| ☁️ **Repositorio de Despliegue Render** | [https://github.com/haroldforero31-creator/MercAPP_Deploy](https://github.com/haroldforero31-creator/MercAPP_Deploy) | Producción Main |

---

## 👥 2. Asignación de Integrantes, Roles y Sustentación

| Integrante | Rol en el Proyecto | Responsabilidad Técnica | Asignación SonarCloud |
|------------|---------------------|--------------------------|-----------------------|
| **Harold Yulian Forero** | Líder Técnico & DevOps | Arquitectura por capas, Despliegue en Render, Seguridad P0 (CORS, CSRF JWT, CSP, Lockout 15 min). | `secrets.token_hex(32)` para `SECRET_KEY` criptográfica. |
| **Integrante 2** | DB Engineer & Backend | Modelo de datos (28 tablas relacionales), SQLAlchemy 2.0 ORM, 5 Stored Procedures y 5 Triggers. | Migración `Model.query.get(id)` a `db.session.get(Model, id)`. |
| **Integrante 3** | Security & API Engineer | API REST, Autenticación JWT Bearer, Sanitización de redirecciones, Colección Postman v2.1. | Centralización `sanitize_next_url()` anti Open-Redirect. |
| **Integrante 4** | QA & Quality Engineer | Pruebas unitarias pytest (37 tests, 69% cobertura), SonarCloud Quality Gate, Reportes Excel y Context Managers. | Context Managers `with sqlite3.connect()` y `io.BytesIO()`. |

---

## 📂 3. Inventario de Archivos en esta Carpeta de Entrega

1. **`MercAPP_IS2_Windows.rar`** (80.2 MB)
   - Paquete portable para Windows. Incluye servidor embebido Waitress, base de datos SQLite WAL, plantillas UI y script de ejecución `iniciar_mercapp.bat`.
2. **`MercAPP_IS2_Windows.zip`** (80.5 MB)
   - Misma distribución en formato estándar ZIP para compatibilidad universal sin necesidad de WinRAR.
3. **`Manual_Tecnico_MercAPP.md`**
   - Documentación técnica exhaustiva: arquitectura MVC por capas, stack tecnológico, flujo de datos, 28 tablas de base de datos, seguridad, endpoints y pipeline de CI/CD en GitHub Actions.
4. **`Manual_Usuario_MercAPP.md`**
   - Manual interactivo para el usuario final con guía paso a paso para los 4 roles (Administrador, Cajero, Proveedor, Cliente Storefront) y matriz completa de permisos CRUD.
5. **`Diccionario_Datos_MercAPP.md`**
   - Diccionario de datos formal de las 28 tablas relacionales con especificación de campos, tipos SQL, claves foráneas, restricciones, valores por defecto y diagrama Entidad-Relación Mermaid.
6. **`Guia_Sustentacion_Diapositivas_15Min.md`**
   - Guion cronometrado minuto a minuto para la sustentación oral de 15 minutos, estructura de las 10 diapositivas requeridas y banco de preguntas difíciles con respuestas técnicas de defensa.
7. **`Guia_SonarCloud_4_Integrantes.md`**
   - Manual paso a paso para vincular GitHub con SonarCloud, activar análisis automático, tomar las 3 capturas del Quality Gate y explicar los 4 hallazgos de código corregidos por el equipo.
8. **`MercAPP_API_Postman_Collection.json`**
   - Colección oficial de Postman v2.1 con 13 endpoints probados contra la API en vivo en Render (`https://mercapp-deploy.onrender.com`), variables de entorno dinámicas y token Bearer JWT.
9. **`stored_procedures_triggers.sql`**
   - Script SQL formal para MySQL 8.0+ conteniendo los 5 Stored Procedures y 5 Triggers requeridos por la guía de la asignatura, con sintaxis normalizada `DELIMITER //`.

---

## 🔑 4. Credenciales de Acceso para Pruebas del Evaluador

> [!TIP]
> Puede probar tanto en el entorno en la nube como descargando el paquete de Windows:

### Acceso Web en la Nube (Render):
- **URL:** [https://mercapp-deploy.onrender.com](https://mercapp-deploy.onrender.com)
- **Registro de Tienda Nueva (Flujo Completo):**
  - Haga clic en *"Registrarse"* en la barra superior.
  - El sistema genera un código de verificación OTP enviado a su correo o visible en consola para confirmar la activación.
- **Portal de Proveedores:** [https://mercapp-deploy.onrender.com/proveedor/login](https://mercapp-deploy.onrender.com/proveedor/login)
- **Tienda Virtual (Clientes Online):** [https://mercapp-deploy.onrender.com/tienda](https://mercapp-deploy.onrender.com/tienda)

### Acceso en Escritorio Windows:
1. Descomprima `MercAPP_IS2_Windows.rar`.
2. Ejecute `iniciar_mercapp.bat`.
3. El sistema levantará automáticamente el servidor en el puerto `5000` y abrirá el navegador en `http://127.0.0.1:5000`.

---

## 🧪 5. Métricas de Calidad y Pruebas del Proyecto

- **Pruebas Automatizadas:** 37 pruebas unitarias y de integración (`pytest`).
- **Cobertura de Código Real:** **69%** (superando el umbral de 68% establecido en el Quality Gate de CI).
- **Pipeline de Integración Continua (CI):** GitHub Actions configurado con matriz de Python 3.11 y 3.12 en `.github/workflows/ci.yml`.
- **SonarCloud Quality Gate:** Estado **PASSED** (0 Bugs, 0 Vulnerabilities, A Rating en Security).
- **Seguridad Aplicada:**
  - Hashes criptográficos seguros (`scrypt` y PBKDF2) para contraseñas.
  - Tokens JWT en cabecera `Authorization: Bearer <token>` para consumo de API REST.
  - Tokens CSRF integrados para formularios web de sesión.
  - Encabezados HTTP de seguridad: `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: strict-origin-when-cross-origin`.
  - Bloqueo temporal de cuentas por fuerza bruta: 5 intentos fallidos suspenden la cuenta por 15 minutos exactos (`locked_until`).

